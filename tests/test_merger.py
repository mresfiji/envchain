"""Tests for envchain.merger module."""

import pytest
from envchain.profile import Profile
from envchain.merger import (
    merge_profiles,
    diff_merge_preview,
    MergeError,
    STRATEGY_LAST_WINS,
    STRATEGY_FIRST_WINS,
    STRATEGY_ERROR_ON_CONFLICT,
)


def _make_profile(name, variables, context="local"):
    return Profile(name=name, context=context, variables=variables)


def test_merge_empty_list_returns_empty_profile():
    result = merge_profiles([], output_name="empty", output_context="local")
    assert result.name == "empty"
    assert result.variables == {}


def test_merge_single_profile_returns_copy():
    p = _make_profile("base", {"FOO": "bar", "BAZ": "qux"})
    result = merge_profiles([p], output_name="merged")
    assert result.variables == {"FOO": "bar", "BAZ": "qux"}
    assert result.name == "merged"


def test_merge_last_wins_strategy():
    p1 = _make_profile("base", {"FOO": "base_val", "SHARED": "from_base"})
    p2 = _make_profile("override", {"SHARED": "from_override", "BAR": "new_val"})
    result = merge_profiles([p1, p2], strategy=STRATEGY_LAST_WINS)
    assert result.variables["FOO"] == "base_val"
    assert result.variables["SHARED"] == "from_override"
    assert result.variables["BAR"] == "new_val"


def test_merge_first_wins_strategy():
    p1 = _make_profile("base", {"FOO": "first", "SHARED": "keep_me"})
    p2 = _make_profile("override", {"SHARED": "ignore_me", "BAR": "added"})
    result = merge_profiles([p1, p2], strategy=STRATEGY_FIRST_WINS)
    assert result.variables["SHARED"] == "keep_me"
    assert result.variables["BAR"] == "added"


def test_merge_error_on_conflict_raises():
    p1 = _make_profile("base", {"CONFLICT": "val1"})
    p2 = _make_profile("other", {"CONFLICT": "val2"})
    with pytest.raises(MergeError, match="Conflict"):
        merge_profiles([p1, p2], strategy=STRATEGY_ERROR_ON_CONFLICT)


def test_merge_error_on_conflict_no_conflict_passes():
    p1 = _make_profile("base", {"FOO": "val1"})
    p2 = _make_profile("other", {"BAR": "val2"})
    result = merge_profiles([p1, p2], strategy=STRATEGY_ERROR_ON_CONFLICT)
    assert result.variables == {"FOO": "val1", "BAR": "val2"}


def test_merge_invalid_strategy_raises():
    p = _make_profile("base", {"FOO": "bar"})
    with pytest.raises(MergeError, match="Invalid merge strategy"):
        merge_profiles([p], strategy="unknown_strategy")


def test_merge_output_context_is_set():
    p = _make_profile("base", {"FOO": "bar"})
    result = merge_profiles([p], output_name="out", output_context="production")
    assert result.context == "production"


def test_diff_merge_preview_no_conflict():
    p1 = _make_profile("base", {"FOO": "foo_val"})
    p2 = _make_profile("extra", {"BAR": "bar_val"})
    preview = diff_merge_preview([p1, p2])
    assert preview["FOO"]["source"] == "base"
    assert preview["BAR"]["source"] == "extra"


def test_diff_merge_preview_last_wins_shows_override():
    p1 = _make_profile("base", {"KEY": "original"})
    p2 = _make_profile("override", {"KEY": "replaced"})
    preview = diff_merge_preview([p1, p2], strategy=STRATEGY_LAST_WINS)
    assert preview["KEY"]["value"] == "replaced"
    assert preview["KEY"]["source"] == "override"


def test_diff_merge_preview_invalid_strategy_raises():
    p = _make_profile("base", {"X": "1"})
    with pytest.raises(MergeError):
        diff_merge_preview([p], strategy="bad")
