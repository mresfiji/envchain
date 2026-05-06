"""Tests for envchain.freezer."""

import pytest
from pathlib import Path
from envchain.freezer import FreezeError, FreezeEntry, FreezeStore


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "freeze_index.json"


@pytest.fixture
def store(store_path: Path) -> FreezeStore:
    return FreezeStore(store_path)


def test_freeze_entry_to_dict():
    entry = FreezeEntry(profile_name="prod", context="production", variables={"KEY": "val"}, reason="stable release")
    d = entry.to_dict()
    assert d["profile_name"] == "prod"
    assert d["context"] == "production"
    assert d["variables"] == {"KEY": "val"}
    assert d["reason"] == "stable release"


def test_freeze_entry_from_dict_roundtrip():
    entry = FreezeEntry(profile_name="staging", context="staging", variables={"A": "1"}, reason=None)
    restored = FreezeEntry.from_dict(entry.to_dict())
    assert restored.profile_name == entry.profile_name
    assert restored.variables == entry.variables
    assert restored.reason is None


def test_freeze_creates_entry(store: FreezeStore):
    entry = store.freeze("myprofile", "local", {"FOO": "bar"}, reason="locked")
    assert entry.profile_name == "myprofile"
    assert store.is_frozen("myprofile")


def test_freeze_duplicate_raises(store: FreezeStore):
    store.freeze("myprofile", "local", {"FOO": "bar"})
    with pytest.raises(FreezeError, match="already frozen"):
        store.freeze("myprofile", "local", {"FOO": "baz"})


def test_unfreeze_removes_entry(store: FreezeStore):
    store.freeze("myprofile", "local", {"FOO": "bar"})
    store.unfreeze("myprofile")
    assert not store.is_frozen("myprofile")


def test_unfreeze_missing_raises(store: FreezeStore):
    with pytest.raises(FreezeError, match="not frozen"):
        store.unfreeze("ghost")


def test_get_frozen_entry(store: FreezeStore):
    store.freeze("prod", "production", {"DB": "postgres"}, reason="v2")
    entry = store.get("prod")
    assert entry.variables == {"DB": "postgres"}
    assert entry.reason == "v2"


def test_get_missing_raises(store: FreezeStore):
    with pytest.raises(FreezeError, match="not frozen"):
        store.get("unknown")


def test_list_frozen_returns_all(store: FreezeStore):
    store.freeze("a", "local", {"X": "1"})
    store.freeze("b", "staging", {"Y": "2"})
    names = [e.profile_name for e in store.list_frozen()]
    assert set(names) == {"a", "b"}


def test_persistence_roundtrip(store_path: Path):
    s1 = FreezeStore(store_path)
    s1.freeze("persist", "production", {"TOKEN": "abc"}, reason="pinned")
    s2 = FreezeStore(store_path)
    assert s2.is_frozen("persist")
    entry = s2.get("persist")
    assert entry.variables["TOKEN"] == "abc"
