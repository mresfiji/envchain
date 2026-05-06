"""Tests for envchain.patcher."""

import pytest

from envchain.profile import Profile, ProfileStore
from envchain.patcher import PatchError, PatchResult, patch_profile


@pytest.fixture
def store(tmp_path):
    s = ProfileStore(tmp_path / "profiles.json")
    p = Profile(name="dev", context="local", variables={"DB_HOST": "localhost", "PORT": "5432"})
    s.add(p)
    return s


def test_patch_applies_existing_key(store):
    result = patch_profile(store, "dev", {"PORT": "6000"})
    assert "PORT" in result.applied
    assert result.applied["PORT"] == "6000"
    assert result.previous["PORT"] == "5432"
    assert result.skipped == []


def test_patch_persists_to_store(store):
    patch_profile(store, "dev", {"PORT": "9999"})
    updated = store.get("dev")
    assert updated.variables["PORT"] == "9999"


def test_patch_skips_missing_key_by_default(store):
    result = patch_profile(store, "dev", {"UNKNOWN_KEY": "value"})
    assert "UNKNOWN_KEY" in result.skipped
    assert "UNKNOWN_KEY" not in result.applied


def test_patch_adds_missing_key_when_flag_set(store):
    result = patch_profile(store, "dev", {"NEW_VAR": "hello"}, add_missing=True)
    assert "NEW_VAR" in result.applied
    updated = store.get("dev")
    assert updated.variables["NEW_VAR"] == "hello"


def test_patch_dry_run_does_not_persist(store):
    result = patch_profile(store, "dev", {"PORT": "1111"}, dry_run=True)
    assert result.applied["PORT"] == "1111"
    unchanged = store.get("dev")
    assert unchanged.variables["PORT"] == "5432"


def test_patch_missing_profile_raises(store):
    with pytest.raises(PatchError, match="not found"):
        patch_profile(store, "nonexistent", {"KEY": "val"})


def test_patch_result_has_changes_true(store):
    result = patch_profile(store, "dev", {"PORT": "8080"})
    assert result.has_changes is True


def test_patch_result_has_changes_false_when_all_skipped(store):
    result = patch_profile(store, "dev", {"MISSING": "x"})
    assert result.has_changes is False


def test_patch_summary_includes_patched_count(store):
    result = patch_profile(store, "dev", {"PORT": "7777"})
    assert "1 key(s) patched" in result.summary()


def test_patch_summary_includes_skipped_count(store):
    result = patch_profile(store, "dev", {"PORT": "7777", "GHOST": "x"})
    assert "1 key(s) skipped" in result.summary()


def test_patch_multiple_keys(store):
    result = patch_profile(store, "dev", {"DB_HOST": "remotehost", "PORT": "3306"})
    assert len(result.applied) == 2
    updated = store.get("dev")
    assert updated.variables["DB_HOST"] == "remotehost"
    assert updated.variables["PORT"] == "3306"
