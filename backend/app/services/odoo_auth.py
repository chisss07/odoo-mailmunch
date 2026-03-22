import httpx


async def authenticate_odoo(url: str, db: str, login: str, password: str) -> dict:
    """Authenticate against Odoo. Returns uid, session_id, and whether TOTP is needed."""
    url = url.rstrip("/")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "call",
        "params": {
            "db": db,
            "login": login,
            "password": password,
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{url}/web/session/authenticate", json=payload)
        response.raise_for_status()
        data = response.json()

    result = data.get("result", {})

    if not result.get("uid"):
        raise ValueError("Invalid credentials")

    # Check if 2FA/TOTP is required
    needs_totp = result.get("totp") is True

    # Extract session_id from response cookies or result
    session_id = None
    for cookie_header in response.headers.get_list("set-cookie"):
        if "session_id=" in cookie_header:
            session_id = cookie_header.split("session_id=")[1].split(";")[0]
            break

    if not session_id:
        session_id = result.get("session_id")

    return {
        "uid": result["uid"],
        "session_id": session_id,
        "needs_totp": needs_totp,
    }


async def verify_totp(url: str, session_id: str, totp_code: str) -> dict:
    """Complete TOTP verification step."""
    url = url.rstrip("/")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "call",
        "params": {
            "totp_token": totp_code,
        },
    }

    async with httpx.AsyncClient(cookies={"session_id": session_id}, timeout=30.0) as client:
        response = await client.post(f"{url}/web/login/totp", json=payload)
        response.raise_for_status()
        data = response.json()

    if "error" in data:
        raise ValueError("Invalid TOTP code")

    # Get updated session_id if rotated
    new_session_id = session_id
    for cookie_header in response.headers.get_list("set-cookie"):
        if "session_id=" in cookie_header:
            new_session_id = cookie_header.split("session_id=")[1].split(";")[0]
            break

    return {"session_id": new_session_id}
