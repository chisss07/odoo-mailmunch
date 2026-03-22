import pytest
import xmlrpc.client
import httpx
from unittest.mock import AsyncMock, patch
from app.services.odoo_auth import authenticate_odoo


@pytest.mark.asyncio
async def test_authenticate_success():
    xml_body = xmlrpc.client.dumps((42,), methodresponse=True)
    mock_response = httpx.Response(
        200,
        text=xml_body,
        request=httpx.Request("POST", "https://test.odoo.com/xmlrpc/2/common"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await authenticate_odoo("https://test.odoo.com", "testdb", "user@test.com", "test-api-key")
        assert result["uid"] == 42


@pytest.mark.asyncio
async def test_authenticate_invalid_credentials():
    xml_body = xmlrpc.client.dumps((False,), methodresponse=True)
    mock_response = httpx.Response(
        200,
        text=xml_body,
        request=httpx.Request("POST", "https://test.odoo.com/xmlrpc/2/common"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        with pytest.raises(ValueError, match="Invalid credentials or API key"):
            await authenticate_odoo("https://test.odoo.com", "testdb", "bad@test.com", "wrong-key")
