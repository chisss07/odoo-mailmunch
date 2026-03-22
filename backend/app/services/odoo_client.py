import httpx


class OdooError(Exception):
    pass


class OdooSessionExpired(OdooError):
    pass


class OdooClient:
    def __init__(self, url: str, db: str, uid: int, session_id: str):
        self.url = url.rstrip("/")
        self.db = db
        self.uid = uid
        self._http = httpx.AsyncClient(
            cookies={"session_id": session_id},
            timeout=30.0,
        )

    async def call(self, model: str, method: str, args: list, kwargs: dict | None = None) -> any:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [self.db, self.uid, "unused", model, method, args, kwargs or {}],
            },
        }
        response = await self._http.post(f"{self.url}/jsonrpc", json=payload)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            error_msg = data["error"].get("data", {}).get("message", data["error"].get("message", "Unknown error"))
            if "Session" in str(error_msg) and "expired" in str(error_msg).lower():
                raise OdooSessionExpired(error_msg)
            raise OdooError(error_msg)

        return data.get("result")

    async def search_read(self, model: str, domain: list, fields: list, limit: int = 0, offset: int = 0) -> list:
        kwargs = {"fields": fields}
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
