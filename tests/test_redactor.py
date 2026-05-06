"""Tests for envchain.redactor."""

import pytest

from envchain.profile import Profile
from envchain.redactor import (
    DEFAULT_MASK,
    RedactorError,
    RedactResult,
    _is_sensitive,
    redact_profile,
    redact_variables,
)


# ---------------------------------------------------------------------------
# _is_sensitive
# ---------------------------------------------------------------------------

def test_is_sensitive_detects_password():
    assert _is_sensitive("DB_PASSWORD") is True


def test_is_sensitive_detects_token():
    assert _is_sensitive("GITHUB_TOKEN") is True


def test_is_sensitive_detects_api_key():
    assert _is_sensitive("STRIPE_API_KEY") is True


def test_is_sensitive_safe_key():
    assert _is_sensitive("APP_ENV") is False
    assert _is_sensitive("PORT") is False


# ---------------------------------------------------------------------------
# redact_variables
# ---------------------------------------------------------------------------

def test_redact_variables_masks_sensitive():
    variables = {"DB_PASSWORD": "s3cr3t", "APP_ENV": "production"}
    result = redact_variables(variables)
    assert result.redacted["DB_PASSWORD"] == DEFAULT_MASK
    assert result.redacted["APP_ENV"] == "production"


def test_redact_variables_lists_redacted_keys():
    variables = {"API_KEY": "abc", "SECRET": "xyz", "HOST": "localhost"}
    result = redact_variables(variables)
    assert "API_KEY" in result.redacted_keys
    assert "SECRET" in result.redacted_keys
    assert "HOST" not in result.redacted_keys


def test_redact_variables_custom_mask():
    variables = {"DB_PASSWORD": "s3cr3t"}
    result = redact_variables(variables, mask="<hidden>")
    assert result.redacted["DB_PASSWORD"] == "<hidden>"


def test_redact_variables_extra_keys():
    variables = {"CUSTOM_VAR": "value", "SAFE": "ok"}
    result = redact_variables(variables, extra_keys=["CUSTOM_VAR"])
    assert result.redacted["CUSTOM_VAR"] == DEFAULT_MASK
    assert result.redacted["SAFE"] == "ok"


def test_redact_variables_no_sensitive_returns_unchanged():
    variables = {"HOST": "localhost", "PORT": "5432"}
    result = redact_variables(variables)
    assert result.redacted == variables
    assert result.redacted_keys == []


def test_redact_variables_original_is_unmodified():
    variables = {"DB_PASSWORD": "s3cr3t"}
    result = redact_variables(variables)
    assert result.original["DB_PASSWORD"] == "s3cr3t"


def test_redact_variables_invalid_input_raises():
    with pytest.raises(RedactorError):
        redact_variables("not-a-dict")  # type: ignore


# ---------------------------------------------------------------------------
# RedactResult helpers
# ---------------------------------------------------------------------------

def test_has_redactions_true():
    result = redact_variables({"API_KEY": "abc"})
    assert result.has_redactions() is True


def test_has_redactions_false():
    result = redact_variables({"HOST": "localhost"})
    assert result.has_redactions() is False


def test_summary_with_redactions():
    result = redact_variables({"DB_PASSWORD": "x", "TOKEN": "y"})
    assert "2 sensitive" in result.summary()


def test_summary_no_redactions():
    result = redact_variables({"HOST": "localhost"})
    assert result.summary() == "No sensitive variables detected."


# ---------------------------------------------------------------------------
# redact_profile
# ---------------------------------------------------------------------------

def test_redact_profile_masks_sensitive_variables():
    profile = Profile(name="prod", context="production",
                      variables={"DB_PASSWORD": "secret", "APP_ENV": "prod"})
    result = redact_profile(profile)
    assert result.redacted["DB_PASSWORD"] == DEFAULT_MASK
    assert result.redacted["APP_ENV"] == "prod"
