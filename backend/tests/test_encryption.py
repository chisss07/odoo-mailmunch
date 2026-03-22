import pytest
from app.services.encryption import encrypt, decrypt


def test_encrypt_decrypt_roundtrip():
    plaintext = "my-secret-odoo-session-cookie"
    encrypted = encrypt(plaintext)
    assert encrypted != plaintext
    assert decrypt(encrypted) == plaintext


def test_encrypt_produces_different_ciphertext():
    plaintext = "same-input"
    a = encrypt(plaintext)
    b = encrypt(plaintext)
    # Fernet uses random IV, so ciphertext should differ
    assert a != b


def test_decrypt_invalid_raises():
    with pytest.raises(Exception):
        decrypt("not-valid-fernet-token")
