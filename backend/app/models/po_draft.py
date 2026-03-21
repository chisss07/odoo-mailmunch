from datetime import datetime, timezone
from typing import Optional
import enum
import sqlalchemy as sa
from sqlalchemy import String, DateTime, Text, Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class DraftStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"


class ConfidenceLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class PODraft(Base):
    __tablename__ = "po_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[int] = mapped_column(index=True)
    vendor_odoo_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vendor_name: Mapped[str] = mapped_column(String(500))
    vendor_confidence: Mapped[ConfidenceLevel] = mapped_column(
        sa.Enum(ConfidenceLevel, name="confidencelevel"), default=ConfidenceLevel.low
    )
    line_items: Mapped[str] = mapped_column(Text)
    total_amount: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    expected_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sales_order_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sales_order_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[DraftStatus] = mapped_column(SAEnum(DraftStatus), default=DraftStatus.DRAFT)
    user_id: Mapped[int] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
