import base64
import hashlib
import json
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings


ENCRYPTED_PREFIX = "enc::"


def _build_cipher(secret: str | None = None) -> AESGCM:
    settings = get_settings()
    key_source = (secret or settings.data_encryption_key).encode("utf-8")
    key = hashlib.sha256(key_source).digest()
    return AESGCM(key)


def encrypt_text(value: str | None, secret: str | None = None) -> str | None:
    if value is None:
        return None
    if value == "" or value.startswith(ENCRYPTED_PREFIX):
        return value
    cipher = _build_cipher(secret)
    nonce = os.urandom(12)
    encrypted = cipher.encrypt(nonce, value.encode("utf-8"), None)
    return ENCRYPTED_PREFIX + base64.urlsafe_b64encode(nonce + encrypted).decode("utf-8")


def decrypt_text(value: str | None, secret: str | None = None) -> str | None:
    if value is None or value == "":
        return value
    if not value.startswith(ENCRYPTED_PREFIX):
        return value
    raw = base64.urlsafe_b64decode(value[len(ENCRYPTED_PREFIX) :].encode("utf-8"))
    nonce, encrypted = raw[:12], raw[12:]
    cipher = _build_cipher(secret)
    decrypted = cipher.decrypt(nonce, encrypted, None)
    return decrypted.decode("utf-8")


def encrypt_json(payload: Any, secret: str | None = None) -> str:
    return encrypt_text(json.dumps(payload, ensure_ascii=False), secret) or ""


def decrypt_json(payload: str | None, fallback: Any, secret: str | None = None) -> Any:
    if not payload:
        return fallback
    decrypted = decrypt_text(payload, secret)
    if not decrypted:
        return fallback
    return json.loads(decrypted)
