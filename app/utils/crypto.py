import base64
from hashlib import sha256

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _derive_key(raw: str) -> bytes:
    return base64.urlsafe_b64encode(sha256(raw.encode()).digest())


def get_cipher() -> Fernet:
    settings = get_settings()
    key = _derive_key(settings.app_secret)
    return Fernet(key)


def encrypt(plaintext: str) -> str:
    c = get_cipher()
    return c.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    c = get_cipher()
    return c.decrypt(ciphertext.encode()).decode()
