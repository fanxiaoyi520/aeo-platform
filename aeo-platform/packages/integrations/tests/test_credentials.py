"""Tests for P6-21: Credential encryption (AES-256-GCM)."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from aeo_integrations.amazon.credentials import (
    CredentialEncryptionError,
    CredentialEncryptor,
    decrypt_credential,
    encrypt_credential,
    reset_encryptor,
)


@pytest.fixture(autouse=True)
def _reset() -> Generator[None, None, None]:
    reset_encryptor()
    yield
    reset_encryptor()


def test_encrypt_decrypt_roundtrip() -> None:
    key = "a" * 32
    encryptor = CredentialEncryptor(key)

    plaintext = "my-secret-refresh-token"
    encrypted = encryptor.encrypt(plaintext)
    decrypted = encryptor.decrypt(encrypted)

    assert decrypted == plaintext
    assert encrypted != plaintext


def test_different_encryptions_produce_different_ciphertext() -> None:
    key = "b" * 32
    encryptor = CredentialEncryptor(key)

    plaintext = "same-secret"
    encrypted1 = encryptor.encrypt(plaintext)
    encrypted2 = encryptor.encrypt(plaintext)

    assert encrypted1 != encrypted2
    assert encryptor.decrypt(encrypted1) == plaintext
    assert encryptor.decrypt(encrypted2) == plaintext


def test_wrong_key_fails() -> None:
    encryptor1 = CredentialEncryptor("a" * 32)
    encryptor2 = CredentialEncryptor("b" * 32)

    encrypted = encryptor1.encrypt("secret-data")

    with pytest.raises(CredentialEncryptionError, match="Decryption failed"):
        encryptor2.decrypt(encrypted)


def test_short_key_raises() -> None:
    with pytest.raises(CredentialEncryptionError, match="at least 32 bytes"):
        CredentialEncryptor("short-key")


def test_invalid_base64_decrypt_fails() -> None:
    encryptor = CredentialEncryptor("c" * 32)
    with pytest.raises(CredentialEncryptionError, match="Invalid encrypted data"):
        encryptor.decrypt("not-valid-base64!!!")


def test_too_short_data_fails() -> None:
    import base64

    encryptor = CredentialEncryptor("d" * 32)
    short_data = base64.b64encode(b"tiny").decode("ascii")
    with pytest.raises(CredentialEncryptionError, match="too short"):
        encryptor.decrypt(short_data)


def test_module_level_functions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", "e" * 32)
    from aeo_integrations.amazon import config as config_module

    config_module.get_amazon_settings.cache_clear()
    reset_encryptor()

    encrypted = encrypt_credential("test-token")
    decrypted = decrypt_credential(encrypted)
    assert decrypted == "test-token"


def test_module_level_no_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CREDENTIAL_ENCRYPTION_KEY", raising=False)
    from aeo_integrations.amazon import config as config_module

    config_module.get_amazon_settings.cache_clear()
    reset_encryptor()

    with pytest.raises(CredentialEncryptionError, match="not configured"):
        encrypt_credential("test")
