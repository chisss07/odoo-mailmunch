import pytest
import xmlrpc.client
import httpx
from unittest.mock import AsyncMock, patch
from app.services.odoo_client import OdooClient


@pytest.mark.asyncio
async def test_call_method():
    client = OdooClient(url="https://test.odoo.com", db="testdb", uid=1, api_key="fake-api-key")

    # Build an XML-RPC response body containing the expected result
    xml_body = xmlrpc.client.dumps(([{"id": 1, "name": "Product A"}],), methodresponse=True)
    mock_response = httpx.Response(
        200,
        text=xml_body,
        request=httpx.Request("POST", "https://test.odoo.com/xmlrpc/2/object"),
    )

    with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response):
        result = await client.call("product.product", "search_read", [[]], {"fields": ["name"], "limit": 10})
        assert result == [{"id": 1, "name": "Product A"}]


@pytest.mark.asyncio
async def test_search_read():
    client = OdooClient(url="https://test.odoo.com", db="testdb", uid=1, api_key="fake-api-key")

    xml_body = xmlrpc.client.dumps(([{"id": 1, "name": "Widget"}],), methodresponse=True)
    mock_response = httpx.Response(
        200,
        text=xml_body,
        request=httpx.Request("POST", "https://test.odoo.com/xmlrpc/2/object"),
    )

    with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response):
        result = await client.search_read("product.product", [], ["name"], limit=10)
        assert result == [{"id": 1, "name": "Widget"}]
