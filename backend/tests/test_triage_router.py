import pytest
from datetime import datetime, timedelta, timezone
from app.models.session import UserSession
from app.models.email import Email, EmailSource, EmailStatus, EmailClassification
from app.models.ignore_rule import IgnoreRule
from app.services.encryption import encrypt
from app.services.jwt_service import create_access_token
from sqlalchemy import select


async def _setup_auth(db_session):
    token = create_access_token(user_id=1, odoo_uid=42, odoo_url="https://test.odoo.com")
    session = UserSession(
        user_id=1,
        odoo_uid=42,
        odoo_url="https://test.odoo.com",
        odoo_db="testdb",
        odoo_session_encrypted=encrypt("fake-session"),
        jwt_token=token,
        refresh_token="fake-refresh-triage",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        refresh_expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(session)
    await db_session.commit()
    return {"Authorization": f"Bearer {token}"}


async def _insert_email(db_session, sender="vendor@acme.com", sender_domain="acme.com", status=EmailStatus.TRIAGE):
    email = Email(
        sender=sender,
        sender_domain=sender_domain,
        subject="Test email",
        body_text="Order #123",
        source=EmailSource.PASTE,
        status=status,
        classification=EmailClassification.UNCLASSIFIED,
        user_id=42,
    )
    db_session.add(email)
    await db_session.commit()
    await db_session.refresh(email)
    return email


@pytest.mark.asyncio
async def test_list_triage_empty(client, db_session):
    headers = await _setup_auth(db_session)
    response = await client.get("/api/triage/", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_triage_returns_only_triage_status(client, db_session):
    headers = await _setup_auth(db_session)
    await _insert_email(db_session, status=EmailStatus.TRIAGE)
    await _insert_email(db_session, status=EmailStatus.PROCESSING)
    response = await client.get("/api/triage/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_triage_ignore(client, db_session):
    headers = await _setup_auth(db_session)
    email = await _insert_email(db_session)
    response = await client.post(
        f"/api/triage/{email.id}/action",
        json={"action": "ignore"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["action"] == "ignore"


@pytest.mark.asyncio
async def test_triage_always_ignore_sender_with_domain(client, db_session):
    headers = await _setup_auth(db_session)
    email = await _insert_email(db_session, sender="vendor@acme.com", sender_domain="acme.com")
    response = await client.post(
        f"/api/triage/{email.id}/action",
        json={"action": "always_ignore_sender"},
        headers=headers,
    )
    assert response.status_code == 200
    result = await db_session.execute(select(IgnoreRule))
    rules = result.scalars().all()
    assert len(rules) == 1
    assert rules[0].field.value == "domain"
    assert rules[0].value == "acme.com"


@pytest.mark.asyncio
async def test_triage_always_ignore_sender_without_domain(client, db_session):
    headers = await _setup_auth(db_session)
    email = await _insert_email(db_session, sender="manual-paste", sender_domain="")
    response = await client.post(
        f"/api/triage/{email.id}/action",
        json={"action": "always_ignore_sender"},
        headers=headers,
    )
    assert response.status_code == 200
    result = await db_session.execute(select(IgnoreRule))
    rules = result.scalars().all()
    assert len(rules) == 1
    assert rules[0].field.value == "sender"
    assert rules[0].value == "manual-paste"


@pytest.mark.asyncio
async def test_triage_import_po(client, db_session):
    headers = await _setup_auth(db_session)
    email = await _insert_email(db_session)
    response = await client.post(
        f"/api/triage/{email.id}/action",
        json={"action": "import_po"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["action"] == "import_po"


@pytest.mark.asyncio
async def test_triage_unknown_action(client, db_session):
    headers = await _setup_auth(db_session)
    email = await _insert_email(db_session)
    response = await client.post(
        f"/api/triage/{email.id}/action",
        json={"action": "nonexistent"},
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_triage_not_found(client, db_session):
    headers = await _setup_auth(db_session)
    response = await client.post(
        "/api/triage/9999/action",
        json={"action": "ignore"},
        headers=headers,
    )
    assert response.status_code == 404
