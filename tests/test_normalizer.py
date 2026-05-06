"""Tests for envchain.normalizer."""

import pytest

from envchain.profile import Profile
from envchain.normalizer import (
    NormalizerError,
    NormalizeResult,
    normalize_profile,
)


def _make_profile(variables: dict, name: str = "test", context: str = "local") -> Profile:
    return Profile(name=name, context=context, variables=variables)


def test_normalize_already_clean_profile():
    p = _make_profile({"API_KEY": "abc123", "HOST": "localhost"})
    result = normalize_profile(p)
    assert result.profile.variables == {"API_KEY": "abc123", "HOST": "localhost"}
    assert not result.has_changes
    assert result.summary() == "no changes"


def test_normalize_uppercases_keys():
    p = _make_profile({"api_key": "secret", "host": "localhost"})
    result = normalize_profile(p)
    assert "API_KEY" in result.profile.variables
    assert "HOST" in result.profile.variables
    assert "api_key" not in result.profile.variables
    assert len(result.renamed_keys) == 2


def test_normalize_strips_key_whitespace():
    p = _make_profile({"  TOKEN  ": "value"})
    result = normalize_profile(p)
    assert "TOKEN" in result.profile.variables
    assert "  TOKEN  " not in result.profile.variables
    assert "  TOKEN  " in result.stripped_keys


def test_normalize_strips_value_whitespace():
    p = _make_profile({"SECRET": "  mysecret  "})
    result = normalize_profile(p)
    assert result.profile.variables["SECRET"] == "mysecret"
    assert "SECRET" in result.coerced_values


def test_normalize_preserves_profile_metadata():
    p = _make_profile({"KEY": "val"}, name="myprofile", context="production")
    result = normalize_profile(p)
    assert result.profile.name == "myprofile"
    assert result.profile.context == "production"


def test_normalize_duplicate_after_uppercase_raises():
    p = _make_profile({"key": "first", "KEY": "second"})
    with pytest.raises(NormalizerError, match="Duplicate key"):
        normalize_profile(p)


def test_normalize_has_changes_true_when_renamed():
    p = _make_profile({"db_host": "localhost"})
    result = normalize_profile(p)
    assert result.has_changes is True


def test_normalize_summary_reports_all_changes():
    p = _make_profile({"  api_key  ": "  value  "})
    result = normalize_profile(p)
    summary = result.summary()
    assert "uppercased" in summary
    assert "whitespace-stripped" in summary


def test_normalize_empty_profile():
    p = _make_profile({})
    result = normalize_profile(p)
    assert result.profile.variables == {}
    assert not result.has_changes


def test_normalize_mixed_case_and_whitespace_value():
    p = _make_profile({"mixed_Key": "\t hello \n"})
    result = normalize_profile(p)
    assert result.profile.variables["MIXED_KEY"] == "hello"
    assert result.has_changes
