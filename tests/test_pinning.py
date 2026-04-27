"""Tests for envchain.pinning."""

import pytest
from pathlib import Path
from envchain.pinning import PinEntry, PinStore, PinError


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "pins.json"


@pytest.fixture
def store(store_path: Path) -> PinStore:
    return PinStore(store_path)


def test_pin_entry_to_dict():
    entry = PinEntry(profile_name="prod", snapshot_id="snap-001", note="stable")
    d = entry.to_dict()
    assert d["profile_name"] == "prod"
    assert d["snapshot_id"] == "snap-001"
    assert d["note"] == "stable"


def test_pin_entry_from_dict_roundtrip():
    entry = PinEntry(profile_name="staging", snapshot_id="snap-002")
    restored = PinEntry.from_dict(entry.to_dict())
    assert restored.profile_name == entry.profile_name
    assert restored.snapshot_id == entry.snapshot_id
    assert restored.note is None


def test_pin_and_get(store: PinStore):
    store.pin("prod", "snap-abc", note="v1.0")
    entry = store.get("prod")
    assert entry is not None
    assert entry.snapshot_id == "snap-abc"
    assert entry.note == "v1.0"


def test_is_pinned(store: PinStore):
    assert not store.is_pinned("dev")
    store.pin("dev", "snap-xyz")
    assert store.is_pinned("dev")


def test_unpin_removes_entry(store: PinStore):
    store.pin("staging", "snap-111")
    store.unpin("staging")
    assert store.get("staging") is None


def test_unpin_unknown_raises(store: PinStore):
    with pytest.raises(PinError, match="not pinned"):
        store.unpin("nonexistent")


def test_all_pins_returns_all(store: PinStore):
    store.pin("prod", "snap-1")
    store.pin("dev", "snap-2")
    pins = store.all_pins()
    names = {p.profile_name for p in pins}
    assert names == {"prod", "dev"}


def test_persistence(store_path: Path):
    s1 = PinStore(store_path)
    s1.pin("prod", "snap-persist", note="keep")
    s2 = PinStore(store_path)
    entry = s2.get("prod")
    assert entry is not None
    assert entry.snapshot_id == "snap-persist"
    assert entry.note == "keep"
