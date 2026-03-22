import logging

from sqlalchemy import select

from app.database import async_session
from app.models.email import Email, EmailSource, EmailStatus, EmailClassification
from app.models.settings import AppSettings
from app.services.encryption import decrypt

logger = logging.getLogger(__name__)


async def poll_m365_mailbox(ctx: dict):
    """Poll M365 mailbox for new emails via Microsoft Graph API."""
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
            graph_client = GraphServiceClient(credential)

            folder = settings_map.get("m365_mailbox_folder", "Inbox")

            # Fetch unread messages
            messages = await graph_client.me.mail_folders.by_mail_folder_id(folder).messages.get(
                query_params={"$filter": "isRead eq false", "$top": 20, "$select": "sender,subject,body,hasAttachments"},
            )

            if not messages or not messages.value:
                await credential.close()
                return

            for msg in messages.value:
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
                    user_id=0,  # TODO(Task 12): ARQ worker must reassign to correct user before processing
                )
                db.add(email_record)

                # Mark as read
                await graph_client.me.messages.by_message_id(msg.id).patch({"isRead": True})

            await db.commit()
            logger.info(f"Polled {len(messages.value)} emails from M365")

            await credential.close()

        except Exception as e:
            logger.error(f"M365 poll error: {e}")
