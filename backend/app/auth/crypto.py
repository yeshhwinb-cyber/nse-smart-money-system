from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _key_from_secret(secret: str) -> bytes:
    if not secret:
        raise ValueError("TOKEN_ENCRYPTION_KEY is required for token encryption")
    raw = secret.encode("utf-8")
    if len(raw) >= 32:
        return raw[:32]
    return raw.ljust(32, b"0")


def encrypt_text(value: str, secret: str) -> str:
    key = _key_from_secret(secret)
    nonce = os.urandom(12)
    encrypted = AESGCM(key).encrypt(nonce, value.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + encrypted).decode("ascii")


def decrypt_text(value: str, secret: str) -> str:
    key = _key_from_secret(secret)
    raw = base64.urlsafe_b64decode(value.encode("ascii"))
    nonce, encrypted = raw[:12], raw[12:]
    return AESGCM(key).decrypt(nonce, encrypted, None).decode("utf-8")
