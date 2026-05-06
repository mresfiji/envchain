"""Tests for envchain.duplicator."""

import json
import pytest

from envchain.profile import Profile, ProfileStore
from envchain.duplicator import (
    DuplicateError,
    DuplicateReport,
    find_duplicates,
    find_duplicates_in_store,
)


def _make_profile(name: str, variables: dict, context: str = "local") -> Profile:
    return Profile(name=name, context=context, variables=variables)


@pytest.fixture
def store(tmp_path):
    return ProfileStore(tmp_path / "profiles.json")


def test_no_duplicates_across_disjoint_profiles():
    profiles = [
        _make_profile("a", {"FOO": "1", "BAR": "2"}),
        _make_profile("b", {"BAZ": "3", "QUX": "4"}),
    ]
    report = find_duplicates(profiles)
    assert not report.has_duplicates
    assert report.scanned_profiles == ["a", "b"]


def test_detects_single_duplicate_key():
    profiles = [
        _make_profile("base", {"DB_URL": "local", "PORT": "5432"}),
        _make_profile("override", {"DB_URL": "prod", "SECRET": "x"}),
    ]
    report = find_duplicates(profiles)
    assert report.has_duplicates
    assert "DB_URL" in report.duplicates
    assert set(report.duplicates["DB_URL"]) == {"base", "override"}


def test_detects_multiple_duplicate_keys():
    profiles = [
        _make_profile("p1", {"A": "1", "B": "2", "C": "3"}),
        _make_profile("p2", {"A": "10", "B": "20", "D": "4"}),
    ]
    report = find_duplicates(profiles)
    assert set(report.duplicates.keys()) == {"A", "B"}


def test_duplicate_across_three_profiles():
    profiles = [
        _make_profile("x", {"SHARED": "1"}),
        _make_profile("y", {"SHARED": "2"}),
        _make_profile("z", {"SHARED": "3"}),
    ]
    report = find_duplicates(profiles)
    assert report.duplicates["SHARED"] == ["x", "y", "z"]


def test_summary_no_duplicates():
    report = DuplicateReport(duplicates={}, scanned_profiles=["a", "b"])
    assert "No duplicate" in report.summary()
    assert "2 profile" in report.summary()


def test_summary_with_duplicates():
    report = DuplicateReport(
        duplicates={"FOO": ["alpha", "beta"]},
        scanned_profiles=["alpha", "beta"],
    )
    summary = report.summary()
    assert "FOO" in summary
    assert "alpha" in summary
    assert "beta" in summary


def test_find_duplicates_in_store(store):
    store.add(_make_profile("dev", {"TOKEN": "abc", "HOST": "localhost"}))
    store.add(_make_profile("staging", {"TOKEN": "xyz", "PORT": "8080"}))
    report = find_duplicates_in_store(store, ["dev", "staging"])
    assert "TOKEN" in report.duplicates
    assert "HOST" not in report.duplicates


def test_find_duplicates_in_store_missing_profile_raises(store):
    store.add(_make_profile("only", {"A": "1"}))
    with pytest.raises(DuplicateError, match="ghost"):
        find_duplicates_in_store(store, ["only", "ghost"])


def test_empty_profile_list_returns_empty_report():
    report = find_duplicates([])
    assert not report.has_duplicates
    assert report.scanned_profiles == []
