"""Tests for envchain.stasher."""
import time
import pytest
from pathlib import Path

from envchain.profile import Profile, ProfileStore
from envchain.stasher import StashEntry, StashError, StashStore


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "stash.json"


@pytest.fixture
def profile_store(tmp_path: Path) -> ProfileStore:
    ps = ProfileStore(tmp_path / "profiles.json")
    p = Profile(name="dev", context="local", variables={"DB_HOST": "localhost", "PORT": "5432"})
    ps.add(p)
    return ps


@pytest.fixture
def store(store_path: Path) -> StashStore:
    return StashStore(store_path)


def test_stash_entry_to_dict():
    entry = StashEntry(label="s1", profile_name="dev", variables={"A": "1"}, stashed_at=1000.0, note="test")
    d = entry.to_dict()
    assert d["label"] == "s1"
    assert d["profile_name"] == "dev"
    assert d["variables"] == {"A": "1"}
    assert d["stashed_at"] == 1000.0
    assert d["note"] == "test"


def test_stash_entry_from_dict_roundtrip():
    entry = StashEntry(label="s1", profile_name="dev", variables={"A": "1"}, stashed_at=1000.0)
    assert StashEntry.from_dict(entry.to_dict()).label == "s1"


def test_stash_saves_profile_variables(store: StashStore, profile_store: ProfileStore):
    entry = store.stash("backup", profile_store, "dev")
    assert entry.variables == {"DB_HOST": "localhost", "PORT": "5432"}


def test_stash_duplicate_label_raises(store: StashStore, profile_store: ProfileStore):
    store.stash("backup", profile_store, "dev")
    with pytest.raises(StashError, match="already exists"):
        store.stash("backup", profile_store, "dev")


def test_stash_missing_profile_raises(store: StashStore, profile_store: ProfileStore):
    with pytest.raises(StashError, match="not found"):
        store.stash("x", profile_store, "nonexistent")


def test_pop_restores_variables(store: StashStore, profile_store: ProfileStore):
    store.stash("backup", profile_store, "dev")
    # mutate the live profile
    profile = profile_store.get("dev")
    profile.variables["DB_HOST"] = "remotehost"
    profile_store.add(profile)
    # pop and restore
    store.pop("backup", profile_store, restore=True)
    restored = profile_store.get("dev")
    assert restored.variables["DB_HOST"] == "localhost"


def test_pop_without_restore_does_not_mutate_profile(store: StashStore, profile_store: ProfileStore):
    store.stash("backup", profile_store, "dev")
    profile = profile_store.get("dev")
    profile.variables["DB_HOST"] = "changed"
    profile_store.add(profile)
    store.pop("backup", profile_store, restore=False)
    assert profile_store.get("dev").variables["DB_HOST"] == "changed"


def test_pop_removes_entry(store: StashStore, profile_store: ProfileStore):
    store.stash("backup", profile_store, "dev")
    store.pop("backup", profile_store)
    assert store.get("backup") is None


def test_pop_unknown_label_raises(store: StashStore, profile_store: ProfileStore):
    with pytest.raises(StashError, match="No stash entry"):
        store.pop("ghost", profile_store)


def test_list_returns_entries_sorted_by_time(store: StashStore, profile_store: ProfileStore):
    store.stash("first", profile_store, "dev")
    time.sleep(0.01)
    store.stash("second", profile_store, "dev")
    labels = [e.label for e in store.list()]
    assert labels == ["first", "second"]


def test_persistence_across_instances(store_path: Path, profile_store: ProfileStore):
    s1 = StashStore(store_path)
    s1.stash("snap", profile_store, "dev", note="persisted")
    s2 = StashStore(store_path)
    entry = s2.get("snap")
    assert entry is not None
    assert entry.note == "persisted"
