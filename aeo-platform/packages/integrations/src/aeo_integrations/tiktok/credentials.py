"""TikTok Shop credentials management with encryption."""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class TikTokCredentialEncryptionError(Exception):
    """Raised when encryption or decryption fails."""


class TikTokCredentialEncryptor:
    """AES-256-GCM encryption for TikTok credential storage."""

    def __init__(self, master_key: str) -> None:
        key_bytes = master_key.encode("utf-8")
        if len(key_bytes) < 32:
            msg = "TIKTOK_CREDENTIAL_ENCRYPTION_KEY must be at least 32 bytes"
            raise TikTokCredentialEncryptionError(msg)
        self._key = key_bytes[:32]
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        payload = nonce + ciphertext
        return base64.b64encode(payload).decode("ascii")

    def decrypt(self, encoded: str) -> str:
        try:
            payload = base64.b64decode(encoded)
        except Exception as exc:
            msg = "Invalid encrypted data format"
            raise TikTokCredentialEncryptionError(msg) from exc
        if len(payload) < 12:
            msg = "Invalid encrypted data: too short"
            raise TikTokCredentialEncryptionError(msg)
        nonce = payload[:12]
        ciphertext = payload[12:]
        try:
            plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as exc:
            msg = "Decryption failed: invalid key or corrupted data"
            raise TikTokCredentialEncryptionError(msg) from exc
        return plaintext.decode("utf-8")


_encryptor: TikTokCredentialEncryptor | None = None


def get_encryptor() -> TikTokCredentialEncryptor:
    global _encryptor  # noqa: PLW0603
    if _encryptor is not None:
        return _encryptor
    key = os.environ.get("TIKTOK_CREDENTIAL_ENCRYPTION_KEY")
    if not key:
        msg = "TIKTOK_CREDENTIAL_ENCRYPTION_KEY is not configured"
        raise TikTokCredentialEncryptionError(msg)
    _encryptor = TikTokCredentialEncryptor(key)
    return _encryptor


def encrypt_credential(plaintext: str) -> str:
    return get_encryptor().encrypt(plaintext)


def decrypt_credential(ciphertext: str) -> str:
    return get_encryptor().decrypt(ciphertext)


def reset_encryptor() -> None:
    global _encryptor  # noqa: PLW0603
    _encryptor = None
