"""Tests for envchain.interpolator."""

import pytest

from envchain.interpolator import (
    InterpolationError,
    InterpolationResult,
    interpolate_profile,
    interpolate_value,
)
from envchain.profile import Profile


# ---------------------------------------------------------------------------
# interpolate_value
# ---------------------------------------------------------------------------

def test_interpolate_value_no_placeholders():
    result, count = interpolate_value("hello world", {})
    assert result == "hello world"
    assert count == 0


def test_interpolate_value_simple_substitution():
    result, count = interpolate_value("${HOST}", {"HOST": "localhost"})
    assert result == "localhost"
    assert count == 1


def test_interpolate_value_inline_substitution():
    result, count = interpolate_value("http://${HOST}:${PORT}", {"HOST": "example.com", "PORT": "8080"})
    assert result == "http://example.com:8080"
    assert count == 2


def test_interpolate_value_uses_default_when_missing():
    result, count = interpolate_value("${MISSING:fallback}", {})
    assert result == "fallback"
    assert count == 1


def test_interpolate_value_prefers_context_over_default():
    result, count = interpolate_value("${KEY:default}", {"KEY": "actual"})
    assert result == "actual"
    assert count == 1


def test_interpolate_value_leaves_unresolved_intact():
    result, count = interpolate_value("${UNKNOWN}", {})
    assert result == "${UNKNOWN}"
    assert count == 0


# ---------------------------------------------------------------------------
# interpolate_profile
# ---------------------------------------------------------------------------

def _make_profile(variables: dict, context: str = "local") -> Profile:
    return Profile(name="test", context=context, variables=variables)


def test_interpolate_profile_self_reference():
    profile = _make_profile({"BASE": "http://localhost", "URL": "${BASE}/api"})
    result = interpolate_profile(profile)
    assert result.resolved["URL"] == "http://localhost/api"
    assert result.substitutions >= 1


def test_interpolate_profile_with_external_context():
    profile = _make_profile({"ENDPOINT": "${HOST}/path"})
    result = interpolate_profile(profile, context={"HOST": "example.com"})
    assert result.resolved["ENDPOINT"] == "example.com/path"
    assert not result.has_unresolved


def test_interpolate_profile_unresolved_tracked():
    profile = _make_profile({"VAL": "${GHOST}"})
    result = interpolate_profile(profile)
    assert result.has_unresolved
    assert "GHOST" in result.unresolved


def test_interpolate_profile_strict_raises_on_unresolved():
    profile = _make_profile({"VAL": "${GHOST}"})
    with pytest.raises(InterpolationError, match="GHOST"):
        interpolate_profile(profile, strict=True)


def test_interpolate_profile_strict_passes_when_all_resolved():
    profile = _make_profile({"A": "hello", "B": "${A} world"})
    result = interpolate_profile(profile, strict=True)
    assert result.resolved["B"] == "hello world"


def test_interpolation_result_summary_no_unresolved():
    r = InterpolationResult(substitutions=3)
    assert "3 substitution" in r.summary()
    assert "unresolved" not in r.summary()


def test_interpolation_result_summary_with_unresolved():
    r = InterpolationResult(substitutions=1, unresolved=["MISSING"])
    assert "unresolved" in r.summary()
    assert "MISSING" in r.summary()
