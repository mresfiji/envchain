"""Tests for envchain.comparator."""

import pytest
from envchain.comparator import compare_profiles, format_compare, CompareResult
from envchain.profile import Profile


def _make_profile(name: str, variables: dict) -> Profile:
    return Profile(name=name, context="local", variables=variables)


def test_compare_identical_profiles():
    left = _make_profile("a", {"FOO": "bar", "BAZ": "qux"})
    right = _make_profile("b", {"FOO": "bar", "BAZ": "qux"})
    result = compare_profiles(left, right)
    assert not result.has_differences()
    assert result.unchanged == {"FOO": "bar", "BAZ": "qux"}


def test_compare_detects_only_in_left():
    left = _make_profile("a", {"FOO": "bar", "EXTRA": "only"})
    right = _make_profile("b", {"FOO": "bar"})
    result = compare_profiles(left, right)
    assert result.has_differences()
    assert "EXTRA" in result.only_in_left
    assert result.only_in_right == {}


def test_compare_detects_only_in_right():
    left = _make_profile("a", {"FOO": "bar"})
    right = _make_profile("b", {"FOO": "bar", "NEW": "val"})
    result = compare_profiles(left, right)
    assert result.has_differences()
    assert "NEW" in result.only_in_right
    assert result.only_in_left == {}


def test_compare_detects_changed_values():
    left = _make_profile("a", {"FOO": "old"})
    right = _make_profile("b", {"FOO": "new"})
    result = compare_profiles(left, right)
    assert result.has_differences()
    assert result.changed["FOO"] == ("old", "new")


def test_compare_summary_no_differences():
    left = _make_profile("a", {"K": "v"})
    right = _make_profile("b", {"K": "v"})
    result = compare_profiles(left, right)
    assert result.summary() == "1 unchanged"


def test_compare_summary_with_differences():
    left = _make_profile("a", {"A": "1", "B": "old"})
    right = _make_profile("b", {"B": "new", "C": "3"})
    result = compare_profiles(left, right)
    summary = result.summary()
    assert "only in 'a'" in summary
    assert "only in 'b'" in summary
    assert "changed" in summary


def test_format_compare_masks_values():
    left = _make_profile("a", {"SECRET": "mysecret"})
    right = _make_profile("b", {"SECRET": "other"})
    result = compare_profiles(left, right)
    lines = format_compare(result, mask_values=True)
    assert any("***" in line for line in lines)
    assert not any("mysecret" in line for line in lines)


def test_format_compare_shows_values_when_unmasked():
    left = _make_profile("a", {"KEY": "val1"})
    right = _make_profile("b", {"KEY": "val2"})
    result = compare_profiles(left, right)
    lines = format_compare(result, mask_values=False)
    assert any("val1" in line for line in lines)
    assert any("val2" in line for line in lines)


def test_format_compare_prefixes():
    left = _make_profile("a", {"ONLY_L": "x", "SHARED": "same"})
    right = _make_profile("b", {"ONLY_R": "y", "SHARED": "same"})
    result = compare_profiles(left, right)
    lines = format_compare(result, mask_values=False)
    prefixes = [line[0] for line in lines]
    assert "<" in prefixes
    assert ">" in prefixes
    assert " " in prefixes
