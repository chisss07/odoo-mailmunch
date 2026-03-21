from datetime import datetime, timezone
import enum
from sqlalchemy import String, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class RuleField(str, enum.Enum):
    SENDER = "sender"
    DOMAIN = "domain"
    SUBJECT = "subject"


class MatchType(str, enum.Enum):
    EXACT = "exact"
    CONTAINS = "contains"
    REGEX = "regex"


class IgnoreRule(Base):
    __tablename__ = "ignore_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    field: Mapped[RuleField] = mapped_column(SAEnum(RuleField))
    match_type: Mapped[MatchType] = mapped_column(SAEnum(MatchType))
    value: Mapped[str] = mapped_column(String(500))
    user_id: Mapped[int] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
