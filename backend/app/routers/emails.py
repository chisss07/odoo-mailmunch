import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.session import UserSession
from app.models.email import Email, EmailSource, EmailStatus, EmailClassification
from app.services.text_extractor import extract_text_from_eml, extract_text_from_pdf, extract_text_from_xlsx, html_to_text
from app.config import settings

router = APIRouter(prefix="/api/emails", tags=["emails"])


class PasteRequest(BaseModel):
    text: str


class InboundEmailWebhook(BaseModel):
    sender: str = ""
    subject: str = ""
    body_plain: str = ""
    body_html: str = ""


@router.post("/paste")
async def paste_email(
    req: PasteRequest,
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    email_record = Email(
        sender="manual-paste",
        sender_domain="",
        subject="Pasted content",
        body_text=req.text,
        source=EmailSource.PASTE,
        status=EmailStatus.PROCESSING,
        classification=EmailClassification.UNCLASSIFIED,
        user_id=user.odoo_uid,
    )
    db.add(email_record)
    await db.commit()
    await db.refresh(email_record)
    return {"status": "processing", "email_id": email_record.id}


@router.post("/upload")
async def upload_email(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    content = await file.read()
    filename = file.filename or "unknown"

    if filename.endswith((".eml", ".msg")):
        parsed = extract_text_from_eml(content)
        sender = parsed["sender"]
        subject = parsed["subject"]
        body = parsed["body"]
        html_body = parsed.get("html_body")
        attachments = parsed.get("attachments", [])
    elif filename.endswith(".pdf") or filename.endswith(".xlsx"):
        # Save to temp file for extraction, then clean up
        import tempfile
        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            if filename.endswith(".pdf"):
                body = extract_text_from_pdf(tmp_path)
            else:
                body = extract_text_from_xlsx(tmp_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract text from {filename}: {e}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)
        sender = "file-upload"
        subject = filename
        html_body = None
        attachments = []
    else:
        sender = "file-upload"
        subject = filename
        body = content.decode("utf-8", errors="replace")
        html_body = None
        attachments = []

    sender_domain = sender.split("@")[-1].split(">")[0] if "@" in sender else ""

    attachment_paths = []
    for att in attachments:
        att_dir = Path(settings.attachment_dir) / str(user.odoo_uid)
        att_dir.mkdir(parents=True, exist_ok=True)
        att_path = att_dir / att["filename"]
        att_path.write_bytes(att["data"])
        attachment_paths.append(str(att_path))

    email_record = Email(
        sender=sender,
        sender_domain=sender_domain,
        subject=subject,
        body_text=body,
        body_html=html_body,
        attachment_paths=json.dumps(attachment_paths) if attachment_paths else None,
        source=EmailSource.UPLOAD,
        status=EmailStatus.PROCESSING,
        classification=EmailClassification.UNCLASSIFIED,
        user_id=user.odoo_uid,
    )
    db.add(email_record)
    await db.commit()
    await db.refresh(email_record)
    return {"status": "processing", "email_id": email_record.id}


@router.post("/inbound-email")
async def inbound_email_webhook(
    req: InboundEmailWebhook,
    db: AsyncSession = Depends(get_db),
):
    sender_domain = req.sender.split("@")[-1] if "@" in req.sender else ""
    body = req.body_plain or html_to_text(req.body_html)

    email_record = Email(
        sender=req.sender,
        sender_domain=sender_domain,
        subject=req.subject,
        body_text=body,
        body_html=req.body_html or None,
        source=EmailSource.FORWARD,
        status=EmailStatus.PROCESSING,
        classification=EmailClassification.UNCLASSIFIED,
        user_id=0,  # TODO(Task 12): ARQ worker must reassign to correct user before processing
    )
    db.add(email_record)
    await db.commit()
    return {"status": "accepted"}


@router.get("/")
async def list_emails(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    query = select(Email).where(Email.user_id == user.odoo_uid)
    if status:
        query = query.where(Email.status == status)
    query = query.order_by(Email.created_at.desc())
    result = await db.execute(query)
    emails = result.scalars().all()
    return [
        {
            "id": e.id,
            "sender": e.sender,
            "subject": e.subject,
            "status": e.status.value,
            "classification": e.classification.value,
            "source": e.source.value,
            "created_at": e.created_at.isoformat(),
        }
        for e in emails
    ]
