"""Tests for envchain.encryptor module."""

import pytest

pytest.importorskip("cryptography", reason="cryptography package not installed")

from envchain.encryptor import Encryptor, EncryptionError, generate_passphrase


@pytest.fixture
def encryptor() -> Encryptor:
    return Encryptor(passphrase="test-secret-passphrase")


def test_encrypt_returns_string(encryptor: Encryptor) -> None:
    token = encryptor.encrypt("hello")
    assert isinstance(token, str)
    assert token != "hello"


def test_decrypt_roundtrip(encryptor: Encryptor) -> None:
    original = "super_secret_value_123"
    token = encryptor.encrypt(original)
    assert encryptor.decrypt(token) == original


def test_different_passphrases_produce_different_keys() -> None:
    enc1 = Encryptor(passphrase="passphrase-one")
    enc2 = Encryptor(passphrase="passphrase-two")
    token = enc1.encrypt("value")
    with pytest.raises(EncryptionError, match="invalid token or wrong passphrase"):
        enc2.decrypt(token)


def test_decrypt_invalid_token_raises(encryptor: Encryptor) -> None:
    with pytest.raises(EncryptionError, match="invalid token or wrong passphrase"):
        encryptor.decrypt("not-a-valid-token")


def test_encrypt_variables(encryptor: Encryptor) -> None:
    variables = {"DB_PASS": "secret", "API_KEY": "abc123"}
    encrypted = encryptor.encrypt_variables(variables)
    assert set(encrypted.keys()) == set(variables.keys())
    for key, token in encrypted.items():
        assert token != variables[key]


def test_decrypt_variables_roundtrip(encryptor: Encryptor) -> None:
    variables = {"DB_PASS": "secret", "API_KEY": "abc123"}
    encrypted = encryptor.encrypt_variables(variables)
    decrypted = encryptor.decrypt_variables(encrypted)
    assert decrypted == variables


def test_encrypt_empty_string(encryptor: Encryptor) -> None:
    token = encryptor.encrypt("")
    assert encryptor.decrypt(token) == ""


def test_generate_passphrase_is_unique() -> None:
    p1 = generate_passphrase()
    p2 = generate_passphrase()
    assert isinstance(p1, str)
    assert len(p1) == 64  # 32 bytes hex-encoded
    assert p1 != p2


def test_encryptor_with_generated_passphrase() -> None:
    passphrase = generate_passphrase()
    enc = Encryptor(passphrase=passphrase)
    value = "MY_SECRET_VALUE"
    assert enc.decrypt(enc.encrypt(value)) == value
