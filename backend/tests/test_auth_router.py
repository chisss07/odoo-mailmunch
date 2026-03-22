import pytest
from unittest.mock import patch, AsyncMock


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
