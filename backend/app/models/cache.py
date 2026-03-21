from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ProductCache(Base):
    __tablename__ = "product_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    odoo_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(500))
    default_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_refreshed: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class VendorCache(Base):
    __tablename__ = "vendor_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    odoo_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(500))
    email: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    email_domain: Mapped[Optional[str]] = mapped_column(String(250), nullable=True, index=True)
    last_refreshed: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class VendorProductMap(Base):
    __tablename__ = "vendor_product_map"

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_odoo_id: Mapped[int] = mapped_column(index=True)
    product_odoo_id: Mapped[int] = mapped_column(index=True)
    vendor_price: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vendor_product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_refreshed: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
