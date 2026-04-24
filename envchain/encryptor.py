"""Encryption and decryption utilities for securing profile variable values."""

import base64
import hashlib
import os
from typing import Dict

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    Fernet = None
    InvalidToken = Exception


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


class Encryptor:
    """Handles symmetric encryption of environment variable values."""

    def __init__(self, passphrase: str) -> None:
        if Fernet is None:
            raise EncryptionError(
                "cryptography package is required for encryption. "
                "Install it with: pip install cryptography"
            )
        self._key = self._derive_key(passphrase)
        self._fernet = Fernet(self._key)

    @staticmethod
    def _derive_key(passphrase: str) -> bytes:
        """Derive a 32-byte Fernet-compatible key from a passphrase."""
        digest = hashlib.sha256(passphrase.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)

    def encrypt(self, value: str) -> str:
        """Encrypt a plaintext string and return a base64-encoded ciphertext."""
        try:
            token = self._fernet.encrypt(value.encode("utf-8"))
            return token.decode("utf-8")
        except Exception as exc:
            raise EncryptionError(f"Encryption failed: {exc}") from exc

    def decrypt(self, token: str) -> str:
        """Decrypt a base64-encoded ciphertext and return the plaintext string."""
        try:
            plaintext = self._fernet.decrypt(token.encode("utf-8"))
            return plaintext.decode("utf-8")
        except InvalidToken as exc:
            raise EncryptionError(
                "Decryption failed: invalid token or wrong passphrase."
            ) from exc
        except Exception as exc:
            raise EncryptionError(f"Decryption failed: {exc}") from exc

    def encrypt_variables(self, variables: Dict[str, str]) -> Dict[str, str]:
        """Encrypt all values in a variables dict, returning a new dict."""
        return {key: self.encrypt(value) for key, value in variables.items()}

    def decrypt_variables(self, variables: Dict[str, str]) -> Dict[str, str]:
        """Decrypt all values in a variables dict, returning a new dict."""
        return {key: self.decrypt(value) for key, value in variables.items()}


def generate_passphrase() -> str:
    """Generate a secure random passphrase (hex-encoded 32 bytes)."""
    return os.urandom(32).hex()
