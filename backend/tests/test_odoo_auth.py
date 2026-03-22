import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.services.odoo_auth import authenticate_odoo


@pytest.mark.asyncio
async def test_authenticate_success_no_2fa():
    mock_response = httpx.Response(
        200,
        json={"jsonrpc": "2.0", "id": 1, "result": {"uid": 42, "session_id": "abc123"}},
        headers={"set-cookie": "session_id=abc123; Path=/"},
        request=httpx.Request("POST", "https://test.odoo.com/web/session/authenticate"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await authenticate_odoo("https://test.odoo.com", "testdb", "user@test.com", "password")
        assert result["uid"] == 42
        assert result["needs_totp"] is False


@pytest.mark.asyncio
async def test_authenticate_invalid_credentials():
    mock_response = httpx.Response(
        200,
        json={"jsonrpc": "2.0", "id": 1, "result": {"uid": False}},
        request=httpx.Request("POST", "https://test.odoo.com/web/session/authenticate"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        with pytest.raises(ValueError, match="Invalid credentials"):
            await authenticate_odoo("https://test.odoo.com", "testdb", "bad@test.com", "wrong")
