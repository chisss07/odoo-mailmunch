import ipaddress
from urllib.parse import urlparse

import httpx
import xmlrpc.client


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
        if "must not point" in str(e):
            raise


async def authenticate_odoo(url: str, db: str, login: str, credential: str, *, is_api_key: bool = True) -> dict:
    """Authenticate against Odoo via XML-RPC. Returns uid."""
    _validate_odoo_url(url)
    url = url.rstrip("/")

    xml_args = (db, login, credential, {})
    body = xmlrpc.client.dumps(xml_args, "authenticate")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{url}/xmlrpc/2/common",
                content=body,
                headers={"Content-Type": "text/xml"},
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise ValueError(f"Odoo returned HTTP {e.response.status_code}. Check your Odoo URL.")
    except httpx.ConnectError:
        raise ValueError("Cannot connect to Odoo. Check your URL.")
    except httpx.TimeoutException:
        raise ValueError("Connection to Odoo timed out.")

    try:
        result = xmlrpc.client.loads(response.text)
        uid = result[0][0]
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"XML-RPC parse error: {e}, response: {response.text[:500]}")
        raise ValueError(f"Unexpected Odoo response: {e}")

    if not uid:
        if is_api_key:
            raise ValueError("Invalid credentials or API key")
        raise ValueError(
            "Invalid credentials. If you have 2FA/TOTP enabled, "
            "password login is not supported — use an API key instead."
        )

    return {"uid": uid}
