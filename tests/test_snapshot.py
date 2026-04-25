"""Tests for envchain.snapshot."""

import json
from pathlib import Path

import pytest

from envchain.snapshot import Snapshot, SnapshotError, SnapshotStore


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "snapshots.json"


@pytest.fixture
def store(store_path: Path) -> SnapshotStore:
    return SnapshotStore(store_path)


def _make_snapshot(name: str = "snap1") -> Snapshot:
    return Snapshot(
        name=name,
        profiles={"local": {"DB_HOST": "localhost", "PORT": "5432"}},
        description="test snapshot",
    )


def test_snapshot_to_dict():
    snap = _make_snapshot()
    d = snap.to_dict()
    assert d["name"] == "snap1"
    assert d["profiles"]["local"]["DB_HOST"] == "localhost"
    assert "created_at" in d


def test_snapshot_from_dict():
    data = {
        "name": "snap2",
        "profiles": {"prod": {"API_KEY": "secret"}},
        "created_at": "2024-01-01T00:00:00+00:00",
        "description": "prod snap",
    }
    snap = Snapshot.from_dict(data)
    assert snap.name == "snap2"
    assert snap.profiles["prod"]["API_KEY"] == "secret"


def test_save_and_get_snapshot(store: SnapshotStore):
    snap = _make_snapshot()
    store.save_snapshot(snap)
    retrieved = store.get_snapshot("snap1")
    assert retrieved.name == "snap1"
    assert retrieved.profiles["local"]["PORT"] == "5432"


def test_get_missing_snapshot_raises(store: SnapshotStore):
    with pytest.raises(SnapshotError, match="not found"):
        store.get_snapshot("nonexistent")


def test_save_empty_name_raises(store: SnapshotStore):
    snap = Snapshot(name="", profiles={})
    with pytest.raises(SnapshotError, match="must not be empty"):
        store.save_snapshot(snap)


def test_list_snapshots_sorted(store: SnapshotStore):
    s1 = Snapshot(name="a", profiles={}, created_at="2024-01-01T00:00:00+00:00")
    s2 = Snapshot(name="b", profiles={}, created_at="2024-06-01T00:00:00+00:00")
    store.save_snapshot(s2)
    store.save_snapshot(s1)
    names = [s.name for s in store.list_snapshots()]
    assert names == ["a", "b"]


def test_delete_snapshot(store: SnapshotStore):
    store.save_snapshot(_make_snapshot())
    store.delete_snapshot("snap1")
    assert store.list_snapshots() == []


def test_delete_missing_snapshot_raises(store: SnapshotStore):
    with pytest.raises(SnapshotError, match="not found"):
        store.delete_snapshot("ghost")


def test_persistence_across_instances(store_path: Path):
    s1 = SnapshotStore(store_path)
    s1.save_snapshot(_make_snapshot("persist_snap"))
    s2 = SnapshotStore(store_path)
    assert s2.get_snapshot("persist_snap").description == "test snapshot"
