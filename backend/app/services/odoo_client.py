import xmlrpc.client
from typing import Any

import httpx


class OdooError(Exception):
    pass


class OdooAuthError(OdooError):
    pass


# Keep for backwards compat in error handling
OdooSessionExpired = OdooAuthError


class OdooClient:
    """Odoo XML-RPC client using API key authentication (stateless, no session cookies)."""

    def __init__(self, url: str, db: str, uid: int, api_key: str):
        self.url = url.rstrip("/")
        self.db = db
        self.uid = uid
        self.api_key = api_key
        self._http = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def call(self, model: str, method: str, args: list, kwargs: dict | None = None) -> Any:
        """Execute an Odoo RPC call via XML-RPC object endpoint."""
        xml_args = (self.db, self.uid, self.api_key, model, method, args, kwargs or {})
        body = xmlrpc.client.dumps(xml_args, "execute_kw")

        response = await self._http.post(
            f"{self.url}/xmlrpc/2/object",
            content=body,
            headers={"Content-Type": "text/xml"},
        )
        response.raise_for_status()

        result = xmlrpc.client.loads(response.text)
        # xmlrpc.client.loads returns (params_tuple, method_name)
        return result[0][0]

    async def search_read(self, model: str, domain: list, fields: list, limit: int = 0, offset: int = 0) -> list:
        kwargs: dict[str, Any] = {"fields": fields}
        if limit:
            kwargs["limit"] = limit
        if offset:
            kwargs["offset"] = offset
        return await self.call(model, "search_read", [domain], kwargs)

    async def create(self, model: str, values: dict) -> int:
        return await self.call(model, "create", [values])

    async def write(self, model: str, ids: list[int], values: dict) -> bool:
        return await self.call(model, "write", [ids, values])

    async def close(self):
        await self._http.aclose()
