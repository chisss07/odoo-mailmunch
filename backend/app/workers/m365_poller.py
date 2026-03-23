import logging

from sqlalchemy import select

from app.database import async_session
from app.models.email import Email, EmailSource, EmailStatus, EmailClassification
from app.models.settings import AppSettings
from app.services.encryption import decrypt

logger = logging.getLogger(__name__)


async def poll_m365_mailbox(ctx: dict):
    """Poll M365 mailbox for new emails via Microsoft Graph API.

    Uses read-only access (Mail.Read). De-duplicates by storing the Graph
    message ID in email.external_id so already-imported messages are skipped.
    """
    async with async_session() as db:
        # Get M365 settings
        result = await db.execute(select(AppSettings).where(AppSettings.key.in_([
            "m365_tenant_id", "m365_client_id", "m365_client_secret", "m365_mailbox_folder",
        ])))
        settings_map = {}
        for s in result.scalars().all():
            if s.is_secret and s.value_encrypted:
                settings_map[s.key] = decrypt(s.value_encrypted)
            else:
                settings_map[s.key] = s.value_plain

        if not all(k in settings_map for k in ["m365_tenant_id", "m365_client_id", "m365_client_secret"]):
            logger.debug("M365 not configured, skipping poll")
            return

        try:
            from azure.identity.aio import ClientSecretCredential
            from msgraph import GraphServiceClient

            credential = ClientSecretCredential(
                tenant_id=settings_map["m365_tenant_id"],
                client_id=settings_map["m365_client_id"],
                client_secret=settings_map["m365_client_secret"],
            )
            try:
                graph_client = GraphServiceClient(credential)

                folder = settings_map.get("m365_mailbox_folder", "Inbox")

                # Fetch recent messages (read-only — no write permissions needed)
                messages = await graph_client.me.mail_folders.by_mail_folder_id(folder).messages.get(
                    query_params={"$top": 20, "$select": "id,sender,subject,body,hasAttachments", "$orderby": "receivedDateTime desc"},
                )

                if not messages or not messages.value:
                    return

                # Collect Graph message IDs to check which are already imported
                graph_ids = [msg.id for msg in messages.value if msg.id]
                existing_result = await db.execute(
                    select(Email.external_id).where(Email.external_id.in_(graph_ids))
                )
                already_imported = set(existing_result.scalars().all())

                imported_count = 0
                for msg in messages.value:
                    if not msg.id or msg.id in already_imported:
                        continue

                    sender = msg.sender.email_address.address if msg.sender else ""
                    sender_domain = sender.split("@")[-1] if "@" in sender else ""

                    email_record = Email(
                        sender=sender,
                        sender_domain=sender_domain,
                        subject=msg.subject or "",
                        body_text=msg.body.content if msg.body else "",
                        source=EmailSource.M365,
                        status=EmailStatus.PROCESSING,
                        classification=EmailClassification.UNCLASSIFIED,
                        external_id=msg.id,
                        user_id=0,  # TODO: resolve user from M365 settings
                    )
                    db.add(email_record)
                    imported_count += 1

                if imported_count:
                    await db.commit()
                    logger.info(f"Imported {imported_count} new emails from M365 (skipped {len(already_imported)} already imported)")
                else:
                    logger.debug("No new emails from M365")

            finally:
                await credential.close()

        except ImportError:
            logger.error("M365 SDK not installed (azure-identity, msgraph-sdk)")
        except Exception:
            logger.error("M365 poll error", exc_info=True)
