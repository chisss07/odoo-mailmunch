import ipaddress
from http.cookies import SimpleCookie
from urllib.parse import urlparse

import httpx


def _validate_odoo_url(url: str) -> None:
    """Reject non-HTTPS and private/loopback addresses."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Odoo URL must use HTTPS")
    hostname = parsed.hostname or ""
    # Block loopback
    if hostname in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Odoo URL must not point to localhost")
    # Block RFC-1918 ranges (basic check)
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private:
            raise ValueError("Odoo URL must not point to a private IP address")
    except ValueError as e:
        # If it's not an IP address (hostname), that's fine -- only raise if it was a private IP check
        if "must not point" in str(e):
            raise


def _extract_session_id(response_headers, fallback_result: dict) -> str | None:
    """Extract session_id from Set-Cookie headers."""
    for cookie_header in response_headers.get_list("set-cookie"):
        cookie = SimpleCookie()
        try:
            cookie.load(cookie_header)
            if "session_id" in cookie:
                return cookie["session_id"].value
        except Exception:
            continue
    return fallback_result.get("session_id")


async def authenticate_odoo(url: str, db: str, login: str, password: str) -> dict:
    """Authenticate against Odoo. Returns uid, session_id, and whether TOTP is needed."""
    _validate_odoo_url(url)
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
    session_id = _extract_session_id(response.headers, result)

    return {
        "uid": result["uid"],
        "session_id": session_id,
        "needs_totp": needs_totp,
    }


async def verify_totp(url: str, session_id: str, totp_code: str) -> dict:
    """Complete TOTP verification step."""
    _validate_odoo_url(url)
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
    new_session_id = _extract_session_id(response.headers, {}) or session_id

    return {"session_id": new_session_id}
