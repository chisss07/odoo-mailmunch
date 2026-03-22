import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock

from app.models.session import UserSession
from app.services.encryption import encrypt
from app.services.jwt_service import create_access_token, create_refresh_token


@pytest.mark.asyncio
async def test_login_success_no_2fa(client):
    mock_auth = AsyncMock(return_value={"uid": 42, "session_id": "abc123", "needs_totp": False})

    with patch("app.routers.auth.authenticate_odoo", mock_auth):
        response = await client.post("/api/auth/login", json={
            "odoo_url": "https://test.odoo.com",
            "database": "testdb",
            "email": "user@test.com",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["needs_totp"] is False


@pytest.mark.asyncio
async def test_login_needs_totp(client):
    mock_auth = AsyncMock(return_value={"uid": 42, "session_id": "abc123", "needs_totp": True})

    with patch("app.routers.auth.authenticate_odoo", mock_auth):
        response = await client.post("/api/auth/login", json={
            "odoo_url": "https://test.odoo.com",
            "database": "testdb",
            "email": "user@test.com",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["needs_totp"] is True
        assert "totp_session" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    mock_auth = AsyncMock(side_effect=ValueError("Invalid credentials"))

    with patch("app.routers.auth.authenticate_odoo", mock_auth):
        response = await client.post("/api/auth/login", json={
            "odoo_url": "https://test.odoo.com",
            "database": "testdb",
            "email": "bad@test.com",
            "password": "wrong",
        })
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_deletes_session(client, db_session):
    now = datetime.now(timezone.utc)
    access_token = create_access_token(user_id=1, odoo_uid=1, odoo_url="https://test.odoo.com")
    refresh_token = create_refresh_token(user_id=1)
    session = UserSession(
        user_id=1,
        odoo_uid=1,
        odoo_url="https://test.odoo.com",
        odoo_db="testdb",
        odoo_session_encrypted=encrypt("session-xyz"),
        jwt_token=access_token,
        refresh_token=refresh_token,
        expires_at=now + timedelta(minutes=30),
        refresh_expires_at=now + timedelta(days=7),
    )
    db_session.add(session)
    await db_session.commit()

    response = await client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # Confirm the row is gone
    from sqlalchemy import select
    result = await db_session.execute(select(UserSession).where(UserSession.jwt_token == access_token))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_refresh_returns_new_tokens(client, db_session):
    now = datetime.now(timezone.utc)
    access_token = create_access_token(user_id=2, odoo_uid=2, odoo_url="https://test.odoo.com")
    refresh_token = create_refresh_token(user_id=2)
    session = UserSession(
        user_id=2,
        odoo_uid=2,
        odoo_url="https://test.odoo.com",
        odoo_db="testdb",
        odoo_session_encrypted=encrypt("session-abc"),
        jwt_token=access_token,
        refresh_token=refresh_token,
        expires_at=now + timedelta(minutes=30),
        refresh_expires_at=now + timedelta(days=7),
    )
    db_session.add(session)
    await db_session.commit()

    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["needs_totp"] is False
    # New tokens must differ from the originals
    assert data["access_token"] != access_token
    assert data["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client):
    response = await client.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer this.is.not.a.valid.token"},
    )
    assert response.status_code == 401
