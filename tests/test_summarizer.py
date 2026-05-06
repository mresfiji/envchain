"""Tests for envchain.summarizer."""

import json
import pytest

from envchain.profile import Profile, ProfileStore
from envchain.summarizer import (
    ProfileSummary,
    StoreSummary,
    summarize_profile,
    summarize_store,
)


def _make_profile(name: str, context: str = "local", **vars_) -> Profile:
    return Profile(name=name, context=context, variables=dict(vars_))


@pytest.fixture
def tmp_store(tmp_path):
    return ProfileStore(tmp_path / "profiles.json")


# --- summarize_profile ---

def test_summarize_profile_basic():
    p = _make_profile("web", "local", HOST="localhost", PORT="8080")
    s = summarize_profile(p)
    assert s.name == "web"
    assert s.context == "local"
    assert s.variable_count == 2
    assert "HOST" in s.variable_names
    assert "PORT" in s.variable_names
    assert s.has_empty_values is False
    assert s.note is None


def test_summarize_profile_detects_empty_value():
    p = _make_profile("web", "local", HOST="localhost", SECRET="")
    s = summarize_profile(p)
    assert s.has_empty_values is True


def test_summarize_profile_with_note():
    p = _make_profile("web", "local", HOST="localhost")
    s = summarize_profile(p, note="review pending")
    assert s.note == "review pending"


def test_summarize_profile_empty_variables():
    p = _make_profile("empty", "staging")
    s = summarize_profile(p)
    assert s.variable_count == 0
    assert s.variable_names == []
    assert s.has_empty_values is False


# --- ProfileSummary.short / detail ---

def test_profile_summary_short_no_flags():
    s = ProfileSummary(name="api", context="prod", variable_count=3, variable_names=["A", "B", "C"])
    assert "api" in s.short()
    assert "prod" in s.short()
    assert "3" in s.short()
    assert "empty" not in s.short()


def test_profile_summary_short_with_empty_flag():
    s = ProfileSummary(name="api", context="prod", variable_count=1, has_empty_values=True)
    assert "has empty values" in s.short()


def test_profile_summary_detail_includes_all_fields():
    s = ProfileSummary(
        name="db", context="staging", variable_count=2,
        variable_names=["DB_HOST", "DB_PORT"], note="needs rotation"
    )
    detail = s.detail()
    assert "db" in detail
    assert "staging" in detail
    assert "DB_HOST" in detail
    assert "needs rotation" in detail


# --- summarize_store ---

def test_summarize_store_empty(tmp_store):
    result = summarize_store(tmp_store)
    assert result.total_profiles == 0
    assert result.profiles == []
    assert result.contexts == []


def test_summarize_store_counts_profiles(tmp_store):
    tmp_store.add_profile(_make_profile("web", "local", HOST="h"))
    tmp_store.add_profile(_make_profile("db", "staging", DB="d"))
    result = summarize_store(tmp_store)
    assert result.total_profiles == 2
    assert len(result.profiles) == 2


def test_summarize_store_short_lists_contexts(tmp_store):
    tmp_store.add_profile(_make_profile("web", "local", A="1"))
    tmp_store.add_profile(_make_profile("db", "production", B="2"))
    result = summarize_store(tmp_store)
    short = result.short()
    assert "local" in short
    assert "production" in short
    assert "2" in short
