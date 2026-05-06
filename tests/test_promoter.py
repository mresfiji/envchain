"""Tests for envchain.promoter."""

import pytest

from envchain.profile import Profile, ProfileStore
from envchain.promoter import PromotionError, promote_profile


@pytest.fixture()
def store(tmp_path):
    s = ProfileStore(tmp_path / "profiles.json")
    s.add(Profile(name="app", context="staging", variables={"HOST": "stg.example.com", "PORT": "8080"}))
    return s


def test_promote_creates_new_profile(store):
    result = promote_profile(store, "app", target_context="production")
    promoted = store.get("app")
    assert promoted is not None
    assert promoted.context == "production"
    assert promoted.variables["HOST"] == "stg.example.com"


def test_promote_returns_correct_result(store):
    result = promote_profile(store, "app", target_context="production")
    assert result.source_name == "app"
    assert result.source_context == "staging"
    assert result.target_context == "production"
    assert result.variables_promoted == 2
    assert result.overwritten is False


def test_promote_with_rename(store):
    result = promote_profile(store, "app", target_context="production", target_name="app-prod")
    assert store.get("app-prod") is not None
    assert result.target_name == "app-prod"


def test_promote_missing_source_raises(store):
    with pytest.raises(PromotionError, match="not found"):
        promote_profile(store, "nonexistent", target_context="production")


def test_promote_existing_target_without_overwrite_raises(store):
    store.add(Profile(name="app", context="production", variables={"HOST": "prod.example.com"}))
    with pytest.raises(PromotionError, match="already exists"):
        promote_profile(store, "app", target_context="production")


def test_promote_existing_target_with_overwrite_succeeds(store):
    store.add(Profile(name="app", context="production", variables={"HOST": "old.example.com"}))
    result = promote_profile(store, "app", target_context="production", overwrite=True)
    assert result.overwritten is True
    assert store.get("app").variables["HOST"] == "stg.example.com"


def test_promote_does_not_mutate_source(store):
    promote_profile(store, "app", target_context="production", target_name="app-prod")
    source = store.get("app")
    assert source.context == "staging"


def test_summary_contains_key_info(store):
    result = promote_profile(store, "app", target_context="production")
    summary = result.summary()
    assert "staging" in summary
    assert "production" in summary
    assert "2" in summary
