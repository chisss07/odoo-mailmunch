import pytest
from app.services.jwt_service import create_access_token, create_refresh_token, verify_token


def test_create_and_verify_access_token():
    token = create_access_token(user_id=1, odoo_uid=42, odoo_url="https://myodoo.com")
    payload = verify_token(token)
    assert payload["user_id"] == 1
    assert payload["odoo_uid"] == 42
    assert payload["odoo_url"] == "https://myodoo.com"
    assert payload["type"] == "access"


def test_create_and_verify_refresh_token():
    token = create_refresh_token(user_id=1)
    payload = verify_token(token)
    assert payload["user_id"] == 1
    assert payload["type"] == "refresh"


def test_verify_invalid_token_raises():
    with pytest.raises(Exception):
        verify_token("invalid.jwt.token")
