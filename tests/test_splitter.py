"""Tests for envchain.splitter."""

import pytest

from envchain.profile import Profile, ProfileStore
from envchain.splitter import SplitError, SplitResult, split_by_prefix


@pytest.fixture
def store(tmp_path):
    s = ProfileStore(tmp_path / "profiles.json")
    source = Profile(
        name="monolith",
        context="production",
        variables={
            "DB_HOST": "db.example.com",
            "DB_PORT": "5432",
            "CACHE_HOST": "redis.example.com",
            "CACHE_TTL": "300",
            "UNTAGGED": "orphan",
        },
    )
    s.add(source)
    return s


def test_split_creates_expected_profiles(store):
    result = split_by_prefix(
        store,
        "monolith",
        {"DB": "db-profile", "CACHE": "cache-profile"},
    )
    assert "db-profile" in result.created
    assert "cache-profile" in result.created


def test_split_strips_prefix_by_default(store):
    split_by_prefix(store, "monolith", {"DB": "db-profile"})
    db = store.get("db-profile")
    assert db is not None
    assert "HOST" in db.variables
    assert "PORT" in db.variables
    assert "DB_HOST" not in db.variables


def test_split_keeps_prefix_when_strip_false(store):
    split_by_prefix(store, "monolith", {"DB": "db-profile"}, strip_prefix=False)
    db = store.get("db-profile")
    assert "DB_HOST" in db.variables


def test_split_reports_skipped_keys(store):
    result = split_by_prefix(
        store,
        "monolith",
        {"DB": "db-profile", "CACHE": "cache-profile"},
    )
    assert "UNTAGGED" in result.skipped_keys


def test_split_inherits_context(store):
    split_by_prefix(store, "monolith", {"DB": "db-profile"})
    db = store.get("db-profile")
    assert db.context == "production"


def test_split_context_override(store):
    split_by_prefix(store, "monolith", {"DB": "db-profile"}, context="staging")
    db = store.get("db-profile")
    assert db.context == "staging"


def test_split_missing_source_raises(store):
    with pytest.raises(SplitError, match="not found"):
        split_by_prefix(store, "nonexistent", {"DB": "db-profile"})


def test_split_skips_empty_bucket(store):
    result = split_by_prefix(store, "monolith", {"NOMATCH": "empty-profile"})
    assert "empty-profile" not in result.created
    assert store.get("empty-profile") is None


def test_split_result_summary_contains_count(store):
    result = split_by_prefix(
        store,
        "monolith",
        {"DB": "db-profile", "CACHE": "cache-profile"},
    )
    summary = result.summary()
    assert "2 profile(s)" in summary
    assert "monolith" in summary


def test_split_result_summary_mentions_skipped(store):
    result = split_by_prefix(
        store,
        "monolith",
        {"DB": "db-profile"},
    )
    summary = result.summary()
    assert "UNTAGGED" in summary or "Skipped" in summary
