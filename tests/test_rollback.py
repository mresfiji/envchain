"""Tests for envchain.rollback."""

from __future__ import annotations

import pytest

from envchain.profile import Profile, ProfileStore
from envchain.history import HistoryStore, HistoryEntry
from envchain.rollback import (
    rollback_profile,
    list_rollback_points,
    RollbackError,
    RollbackResult,
)


@pytest.fixture
def profile_store(tmp_path):
    return ProfileStore(str(tmp_path / "profiles.json"))


@pytest.fixture
def history_store(tmp_path):
    return HistoryStore(str(tmp_path / "history.json"))


def _add_profile(store: ProfileStore, name: str, variables: dict) -> Profile:
    p = Profile(name=name, context="local", variables=variables)
    store.add(p)
    return p


def _add_entry(store: HistoryStore, profile_name: str, variables: dict) -> HistoryEntry:
    entry = store.record(profile_name=profile_name, variables=variables)
    return entry


def test_rollback_restores_variables(profile_store, history_store):
    _add_profile(profile_store, "app", {"KEY": "new_value"})
    entry = _add_entry(history_store, "app", {"KEY": "old_value"})

    result = rollback_profile("app", entry.id, profile_store, history_store)

    assert isinstance(result, RollbackResult)
    assert result.restored_variables == {"KEY": "old_value"}
    assert result.previous_variables == {"KEY": "new_value"}
    assert "KEY" in result.changed_keys


def test_rollback_persists_to_store(profile_store, history_store):
    _add_profile(profile_store, "app", {"KEY": "new_value"})
    entry = _add_entry(history_store, "app", {"KEY": "old_value"})

    rollback_profile("app", entry.id, profile_store, history_store)

    updated = profile_store.get("app")
    assert updated.variables["KEY"] == "old_value"


def test_rollback_unknown_profile_raises(profile_store, history_store):
    entry = _add_entry(history_store, "ghost", {"X": "1"})
    with pytest.raises(RollbackError, match="not found"):
        rollback_profile("ghost", entry.id, profile_store, history_store)


def test_rollback_unknown_entry_raises(profile_store, history_store):
    _add_profile(profile_store, "app", {"KEY": "v"})
    with pytest.raises(RollbackError, match="not found"):
        rollback_profile("app", "nonexistent-id", profile_store, history_store)


def test_rollback_wrong_profile_raises(profile_store, history_store):
    _add_profile(profile_store, "app", {"KEY": "v"})
    entry = _add_entry(history_store, "other", {"KEY": "v"})
    with pytest.raises(RollbackError, match="belongs to profile"):
        rollback_profile("app", entry.id, profile_store, history_store)


def test_changed_keys_empty_when_identical(profile_store, history_store):
    _add_profile(profile_store, "app", {"KEY": "same"})
    entry = _add_entry(history_store, "app", {"KEY": "same"})
    result = rollback_profile("app", entry.id, profile_store, history_store)
    assert result.changed_keys == []


def test_list_rollback_points_returns_entries(history_store):
    _add_entry(history_store, "app", {"A": "1"})
    _add_entry(history_store, "app", {"A": "2"})
    _add_entry(history_store, "other", {"B": "3"})

    points = list_rollback_points("app", history_store)
    assert len(points) == 2
    assert all(e.profile_name == "app" for e in points)


def test_list_rollback_points_respects_limit(history_store):
    for i in range(5):
        _add_entry(history_store, "app", {"I": str(i)})
    points = list_rollback_points("app", history_store, limit=3)
    assert len(points) == 3
