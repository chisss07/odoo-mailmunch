from datetime import datetime, timezone
from typing import Optional
import enum
from sqlalchemy import String, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class EmailStatus(str, enum.Enum):
    TRIAGE = "triage"
    PROCESSING = "processing"
    REVIEWED = "reviewed"
    IGNORED = "ignored"


class EmailSource(str, enum.Enum):
    M365 = "m365"
    FORWARD = "forward"
    UPLOAD = "upload"
    PASTE = "paste"


class EmailClassification(str, enum.Enum):
    PURCHASE_ORDER = "purchase_order"
    SHIPPING_NOTICE = "shipping_notice"
    BILL = "bill"
    UNRELATED = "unrelated"
    UNCLASSIFIED = "unclassified"


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender: Mapped[str] = mapped_column(String(500))
    sender_domain: Mapped[str] = mapped_column(String(250), index=True)
    subject: Mapped[str] = mapped_column(String(1000))
    body_text: Mapped[str] = mapped_column(Text)
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachment_paths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[EmailSource] = mapped_column(SAEnum(EmailSource))
    status: Mapped[EmailStatus] = mapped_column(SAEnum(EmailStatus), default=EmailStatus.TRIAGE, index=True)
    classification: Mapped[EmailClassification] = mapped_column(SAEnum(EmailClassification), default=EmailClassification.UNCLASSIFIED)
    external_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, unique=True)
    user_id: Mapped[int] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
