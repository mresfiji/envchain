"""Tests for envchain.deduplicator."""
import pytest

from envchain.deduplicator import (
    DeduplicateResult,
    DeduplicatorError,
    deduplicate_profile,
)
from envchain.profile import Profile


def _make_profile(variables: dict, name: str = "test", context: str = "local") -> Profile:
    return Profile(name=name, context=context, variables=variables)


def test_no_duplicates_returns_empty_removed():
    p = _make_profile({"A": "1", "B": "2", "C": "3"})
    result = deduplicate_profile(p)
    assert result.has_duplicates is False
    assert result.removed_keys == []
    assert result.deduped_variables == {"A": "1", "B": "2", "C": "3"}


def test_detects_single_duplicate_value():
    p = _make_profile({"A": "same", "B": "other", "C": "same"})
    result = deduplicate_profile(p, keep="first")
    assert result.has_duplicates is True
    assert "C" in result.removed_keys
    assert "A" in result.kept_keys
    assert "C" not in result.deduped_variables
    assert "A" in result.deduped_variables


def test_keep_last_removes_first_occurrence():
    p = _make_profile({"A": "same", "B": "other", "C": "same"})
    result = deduplicate_profile(p, keep="last")
    assert result.has_duplicates is True
    assert "A" in result.removed_keys
    assert "C" in result.kept_keys
    assert "A" not in result.deduped_variables
    assert "C" in result.deduped_variables


def test_multiple_duplicates_all_removed():
    p = _make_profile({"A": "x", "B": "x", "C": "x", "D": "y"})
    result = deduplicate_profile(p, keep="first")
    assert sorted(result.removed_keys) == ["B", "C"]
    assert result.deduped_variables == {"A": "x", "D": "y"}


def test_original_variables_unchanged():
    original = {"A": "dup", "B": "dup"}
    p = _make_profile(dict(original))
    result = deduplicate_profile(p)
    assert result.original_variables == original


def test_summary_no_duplicates():
    p = _make_profile({"A": "1"})
    result = deduplicate_profile(p)
    assert "No duplicate" in result.summary()


def test_summary_with_duplicates():
    p = _make_profile({"A": "v", "B": "v"}, name="myprofile")
    result = deduplicate_profile(p)
    assert "myprofile" in result.summary()
    assert "Removed 1" in result.summary()


def test_invalid_keep_strategy_raises():
    p = _make_profile({"A": "1"})
    with pytest.raises(DeduplicatorError, match="Invalid keep strategy"):
        deduplicate_profile(p, keep="random")


def test_empty_profile_returns_empty_result():
    p = _make_profile({})
    result = deduplicate_profile(p)
    assert result.has_duplicates is False
    assert result.deduped_variables == {}
    assert result.removed_keys == []


def test_result_profile_name_matches():
    p = _make_profile({"K": "v"}, name="staging")
    result = deduplicate_profile(p)
    assert result.profile_name == "staging"
