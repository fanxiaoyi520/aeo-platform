"""P7-11: Tests for TikTok credentials encryption."""

from __future__ import annotations

import os

import pytest
from aeo_integrations.tiktok.credentials import (
    TikTokCredentialEncryptionError,
    TikTokCredentialEncryptor,
    decrypt_credential,
    encrypt_credential,
    get_encryptor,
    reset_encryptor,
)


class TestTikTokCredentialEncryptor:
    def test_encryptor_requires_32_byte_key(self) -> None:
        with pytest.raises(TikTokCredentialEncryptionError, match="at least 32 bytes"):
            TikTokCredentialEncryptor("short_key")

    def test_encrypt_decrypt_roundtrip(self) -> None:
        key = "a" * 32
        encryptor = TikTokCredentialEncryptor(key)

        plaintext = "tiktok_access_token_12345"
        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_produces_different_ciphertext(self) -> None:
        key = "a" * 32
        encryptor = TikTokCredentialEncryptor(key)

        plaintext = "tiktok_access_token"
        encrypted1 = encryptor.encrypt(plaintext)
        encrypted2 = encryptor.encrypt(plaintext)

        assert encrypted1 != encrypted2

    def test_decrypt_with_wrong_key_fails(self) -> None:
        key1 = "a" * 32
        key2 = "b" * 32
        encryptor1 = TikTokCredentialEncryptor(key1)
        encryptor2 = TikTokCredentialEncryptor(key2)

        plaintext = "secret_token"
        encrypted = encryptor1.encrypt(plaintext)

        with pytest.raises(TikTokCredentialEncryptionError, match="Decryption failed"):
            encryptor2.decrypt(encrypted)

    def test_decrypt_invalid_base64_fails(self) -> None:
        key = "a" * 32
        encryptor = TikTokCredentialEncryptor(key)

        with pytest.raises(TikTokCredentialEncryptionError, match="Invalid encrypted data"):
            encryptor.decrypt("not-valid-base64!!!")

    def test_decrypt_too_short_data_fails(self) -> None:
        key = "a" * 32
        encryptor = TikTokCredentialEncryptor(key)

        import base64

        short_data = base64.b64encode(b"short").decode("ascii")
        with pytest.raises(TikTokCredentialEncryptionError, match="too short"):
            encryptor.decrypt(short_data)


class TestGlobalEncryptor:
    def setup_method(self) -> None:
        reset_encryptor()
        if "TIKTOK_CREDENTIAL_ENCRYPTION_KEY" in os.environ:
            del os.environ["TIKTOK_CREDENTIAL_ENCRYPTION_KEY"]

    def teardown_method(self) -> None:
        reset_encryptor()
        if "TIKTOK_CREDENTIAL_ENCRYPTION_KEY" in os.environ:
            del os.environ["TIKTOK_CREDENTIAL_ENCRYPTION_KEY"]

    def test_get_encryptor_without_key_fails(self) -> None:
        with pytest.raises(TikTokCredentialEncryptionError, match="not configured"):
            get_encryptor()

    def test_get_encryptor_with_key_succeeds(self) -> None:
        os.environ["TIKTOK_CREDENTIAL_ENCRYPTION_KEY"] = "a" * 32
        encryptor = get_encryptor()
        assert isinstance(encryptor, TikTokCredentialEncryptor)

    def test_get_encryptor_caches_instance(self) -> None:
        os.environ["TIKTOK_CREDENTIAL_ENCRYPTION_KEY"] = "a" * 32
        encryptor1 = get_encryptor()
        encryptor2 = get_encryptor()
        assert encryptor1 is encryptor2

    def test_encrypt_decrypt_global_functions(self) -> None:
        os.environ["TIKTOK_CREDENTIAL_ENCRYPTION_KEY"] = "a" * 32

        plaintext = "tiktok_secret_123"
        encrypted = encrypt_credential(plaintext)
        decrypted = decrypt_credential(encrypted)

        assert decrypted == plaintext
