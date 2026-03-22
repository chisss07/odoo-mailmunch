import pytest
from datetime import datetime, timedelta, timezone
from app.models.session import UserSession
from app.services.encryption import encrypt
from app.services.jwt_service import create_access_token


async def _insert_session(db_session, token: str):
    session = UserSession(
        user_id=1,
        odoo_uid=42,
        odoo_url="https://test.odoo.com",
        odoo_db="testdb",
        odoo_api_key_encrypted=encrypt("fake-api-key"),
        jwt_token=token,
        refresh_token="fake-refresh-settings",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        refresh_expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(session)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_settings_empty(client, db_session):
    token = create_access_token(user_id=1, odoo_uid=42, odoo_url="https://test.odoo.com")
    await _insert_session(db_session, token)
    response = await client.get("/api/settings", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {}


@pytest.mark.asyncio
async def test_update_and_get_setting(client, db_session):
    token = create_access_token(user_id=1, odoo_uid=42, odoo_url="https://test.odoo.com")
    await _insert_session(db_session, token)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.put(
        "/api/settings",
        json={"key": "sync_interval", "value": "60"},
        headers=headers,
    )
    assert response.status_code == 200

    response = await client.get("/api/settings", headers=headers)
    assert response.status_code == 200
    assert response.json()["sync_interval"] == "60"


@pytest.mark.asyncio
async def test_create_and_list_ignore_rule(client, db_session):
    token = create_access_token(user_id=1, odoo_uid=42, odoo_url="https://test.odoo.com")
    await _insert_session(db_session, token)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/api/settings/ignore-rules",
        json={"field": "domain", "match_type": "exact", "value": "spam.com"},
        headers=headers,
    )
    assert response.status_code == 200
    rule_id = response.json()["id"]

    response = await client.get("/api/settings/ignore-rules", headers=headers)
    assert response.status_code == 200
    rules = response.json()
    assert len(rules) == 1
    assert rules[0]["value"] == "spam.com"

    # Delete the rule
    response = await client.delete(f"/api/settings/ignore-rules/{rule_id}", headers=headers)
    assert response.status_code == 200
