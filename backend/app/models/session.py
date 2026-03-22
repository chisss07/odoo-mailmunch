from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class UserSession(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    odoo_uid: Mapped[int]
    odoo_url: Mapped[str] = mapped_column(String(500))
    odoo_db: Mapped[str] = mapped_column(String(200))
    odoo_api_key_encrypted: Mapped[str] = mapped_column(Text)
    jwt_token: Mapped[str] = mapped_column(Text, unique=True, index=True)
    refresh_token: Mapped[str] = mapped_column(Text, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    refresh_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
