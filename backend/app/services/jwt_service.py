from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from jwt.exceptions import InvalidTokenError

from app.config import settings

ALGORITHM = "HS256"


def create_access_token(user_id: int, odoo_uid: int, odoo_url: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes)
    payload = {
        "user_id": user_id,
        "odoo_uid": odoo_uid,
        "odoo_url": odoo_url,
        "type": "access",
        "exp": expire,
    }
    return pyjwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expiry_days)
    payload = {
        "user_id": user_id,
        "type": "refresh",
        "exp": expire,
    }
    return pyjwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str, expected_type: str | None = None) -> dict:
    try:
        payload = pyjwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}") from e
    if expected_type and payload.get("type") != expected_type:
        raise ValueError(f"Expected token type '{expected_type}', got '{payload.get('type')}'")
    return payload
