"""Tests for envchain.sanitizer."""

import pytest

from envchain.profile import Profile
from envchain.sanitizer import (
    REDACT_PLACEHOLDER,
    SanitizeResult,
    SanitizerError,
    _is_sensitive,
    _mask_value,
    sanitize_profile,
)


def _make_profile(variables: dict) -> Profile:
    return Profile(name="test", context="local", variables=variables)


# --- unit helpers ---

def test_is_sensitive_detects_password():
    assert _is_sensitive("DB_PASSWORD") is True


def test_is_sensitive_detects_token():
    assert _is_sensitive("GITHUB_TOKEN") is True


def test_is_sensitive_detects_api_key():
    assert _is_sensitive("STRIPE_API_KEY") is True


def test_is_sensitive_safe_key():
    assert _is_sensitive("APP_PORT") is False


def test_mask_value_short():
    assert _mask_value("abc", visible_chars=4) == "***"


def test_mask_value_long():
    result = _mask_value("mysecretvalue", visible_chars=4)
    assert result.startswith("myse")
    assert result.endswith("*" * (len("mysecretvalue") - 4))


# --- sanitize_profile: redact mode ---

def test_redact_replaces_sensitive_value():
    profile = _make_profile({"DB_PASSWORD": "hunter2", "APP_PORT": "8080"})
    result = sanitize_profile(profile, mode="redact")
    assert result.sanitized_variables["DB_PASSWORD"] == REDACT_PLACEHOLDER
    assert result.sanitized_variables["APP_PORT"] == "8080"


def test_redact_records_redacted_keys():
    profile = _make_profile({"API_KEY": "abc", "HOST": "localhost"})
    result = sanitize_profile(profile, mode="redact")
    assert "API_KEY" in result.redacted_keys
    assert "HOST" not in result.redacted_keys


def test_redact_with_extra_keys():
    profile = _make_profile({"CUSTOM_FIELD": "sensitive", "OTHER": "value"})
    result = sanitize_profile(profile, mode="redact", extra_keys=["CUSTOM_FIELD"])
    assert result.sanitized_variables["CUSTOM_FIELD"] == REDACT_PLACEHOLDER
    assert "CUSTOM_FIELD" in result.redacted_keys


# --- sanitize_profile: mask mode ---

def test_mask_partially_hides_value():
    profile = _make_profile({"AUTH_TOKEN": "abcdefgh"})
    result = sanitize_profile(profile, mode="mask")
    val = result.sanitized_variables["AUTH_TOKEN"]
    assert val.startswith("abcd")
    assert "*" in val


def test_mask_records_masked_keys():
    profile = _make_profile({"DB_SECRET": "topsecret"})
    result = sanitize_profile(profile, mode="mask")
    assert "DB_SECRET" in result.masked_keys
    assert result.redacted_keys == []


# --- error handling ---

def test_invalid_mode_raises():
    profile = _make_profile({"KEY": "val"})
    with pytest.raises(SanitizerError, match="Unknown sanitize mode"):
        sanitize_profile(profile, mode="scramble")


# --- summary ---

def test_summary_no_sensitive_keys():
    profile = _make_profile({"APP_HOST": "localhost"})
    result = sanitize_profile(profile)
    assert "no sensitive keys" in result.summary()


def test_summary_with_redacted_keys():
    profile = _make_profile({"DB_PASSWORD": "x"})
    result = sanitize_profile(profile, mode="redact")
    assert "redacted" in result.summary()
    assert "DB_PASSWORD" in result.summary()
