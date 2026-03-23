import logging

from sqlalchemy import select

from app.database import async_session
from app.models.email import Email, EmailSource, EmailStatus, EmailClassification
from app.models.settings import AppSettings
from app.services.encryption import decrypt

logger = logging.getLogger(__name__)


async def poll_m365_mailbox(ctx: dict):
    """Poll M365 mailbox for new emails via Microsoft Graph API.

    Uses app-only (client credentials) auth with read-only Mail.Read permission.
    Requires m365_mailbox_user to target a specific user's mailbox since /me
    is not available with app-only auth. De-duplicates via external_id.
    """
    async with async_session() as db:
        # Get M365 settings
        result = await db.execute(select(AppSettings).where(AppSettings.key.in_([
            "m365_tenant_id", "m365_client_id", "m365_client_secret",
            "m365_mailbox_user", "m365_mailbox_folder",
        ])))
        settings_map = {}
        for s in result.scalars().all():
            if s.is_secret and s.value_encrypted:
                settings_map[s.key] = decrypt(s.value_encrypted)
            else:
                settings_map[s.key] = s.value_plain

        required = ["m365_tenant_id", "m365_client_id", "m365_client_secret", "m365_mailbox_user"]
        if not all(settings_map.get(k) for k in required):
            logger.debug("M365 not fully configured, skipping poll")
            return

        try:
            from azure.identity.aio import ClientSecretCredential
            from msgraph import GraphServiceClient
            from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import MessagesRequestBuilder

            credential = ClientSecretCredential(
                tenant_id=settings_map["m365_tenant_id"],
                client_id=settings_map["m365_client_id"],
                client_secret=settings_map["m365_client_secret"],
            )
            try:
                graph_client = GraphServiceClient(credential)

                mailbox_user = settings_map["m365_mailbox_user"]
                folder = settings_map.get("m365_mailbox_folder", "Inbox")

                # Use /users/{user} instead of /me for app-only auth
                query_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
                    query_parameters=MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
                        top=20,
                        select=["id", "sender", "subject", "body", "hasAttachments"],
                        orderby=["receivedDateTime desc"],
                    )
                )
                messages = await graph_client.users.by_user_id(mailbox_user).mail_folders.by_mail_folder_id(folder).messages.get(
                    request_configuration=query_config,
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
