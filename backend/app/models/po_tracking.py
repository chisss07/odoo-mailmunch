from datetime import datetime, timezone
from typing import Optional
import enum
import sqlalchemy as sa
from sqlalchemy import String, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class POStatus(str, enum.Enum):
    draft = "draft"
    confirmed = "confirmed"
    received = "received"
    cancelled = "cancelled"


class POTracking(Base):
    __tablename__ = "po_tracking"

    id: Mapped[int] = mapped_column(primary_key=True)
    odoo_po_id: Mapped[int] = mapped_column(index=True)
    odoo_po_name: Mapped[str] = mapped_column(String(100))
    vendor_name: Mapped[str] = mapped_column(String(500))
    status: Mapped[POStatus] = mapped_column(
        sa.Enum(POStatus, name="postatus"), index=True, default=POStatus.draft
    )
    sales_order_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sales_order_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    draft_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_id: Mapped[int] = mapped_column(index=True)
    last_synced: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
