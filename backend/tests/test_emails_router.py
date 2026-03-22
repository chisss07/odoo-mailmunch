import pytest
from datetime import datetime, timedelta, timezone
from app.models.session import UserSession
from app.services.encryption import encrypt
from app.services.jwt_service import create_access_token


@pytest.fixture
def auth_headers(db_session):
    """Create auth headers - note: requires session in DB too."""
    token = create_access_token(user_id=1, odoo_uid=42, odoo_url="https://test.odoo.com")
    return {"Authorization": f"Bearer {token}"}


async def _insert_session(db_session, token: str):
    session = UserSession(
        user_id=1,
        odoo_uid=42,
        odoo_url="https://test.odoo.com",
        odoo_db="testdb",
        odoo_session_encrypted=encrypt("fake-session"),
        jwt_token=token,
        refresh_token="fake-refresh-emails",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        refresh_expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(session)
    await db_session.commit()


@pytest.mark.asyncio
async def test_paste_email(client, db_session):
    token = create_access_token(user_id=1, odoo_uid=42, odoo_url="https://test.odoo.com")
    await _insert_session(db_session, token)

    response = await client.post(
        "/api/emails/paste",
        json={"text": "Order #123 from Acme. Widget A, Qty: 10, $5.00 each. Total: $50.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert "email_id" in data


@pytest.mark.asyncio
async def test_list_emails_empty(client, db_session):
    token = create_access_token(user_id=1, odoo_uid=42, odoo_url="https://test.odoo.com")
    await _insert_session(db_session, token)

    response = await client.get(
        "/api/emails/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == []
