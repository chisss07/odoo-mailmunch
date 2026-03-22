import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.services.odoo_client import OdooClient, OdooError


@pytest.mark.asyncio
async def test_call_method():
    client = OdooClient(url="https://test.odoo.com", db="testdb", uid=1, session_id="fake-session")

    mock_response = httpx.Response(
        200,
        json={"jsonrpc": "2.0", "id": 1, "result": [{"id": 1, "name": "Product A"}]},
        request=httpx.Request("POST", "https://test.odoo.com/jsonrpc"),
    )

    with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response):
        result = await client.call("product.product", "search_read", [[]], {"fields": ["name"], "limit": 10})
        assert result == [{"id": 1, "name": "Product A"}]


@pytest.mark.asyncio
async def test_call_method_error():
    client = OdooClient(url="https://test.odoo.com", db="testdb", uid=1, session_id="fake-session")

    mock_response = httpx.Response(
        200,
        json={"jsonrpc": "2.0", "id": 1, "error": {"message": "Access denied", "data": {"message": "Access denied"}}},
        request=httpx.Request("POST", "https://test.odoo.com/jsonrpc"),
    )

    with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response):
        with pytest.raises(OdooError, match="Access denied"):
            await client.call("product.product", "search_read", [[]], {})
