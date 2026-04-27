"""Tests for envchain.history module."""

import json
from pathlib import Path

import pytest

from envchain.history import HistoryEntry, HistoryStore


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "history.json"


@pytest.fixture
def store(store_path: Path) -> HistoryStore:
    return HistoryStore(store_path)


def _make_entry(name: str = "base", context: str = "local") -> HistoryEntry:
    return HistoryEntry(
        profile_name=name,
        context=context,
        variables={"KEY": "value"},
    )


def test_history_entry_to_dict():
    entry = _make_entry()
    d = entry.to_dict()
    assert d["profile_name"] == "base"
    assert d["context"] == "local"
    assert d["variables"] == {"KEY": "value"}
    assert "timestamp" in d
    assert d["note"] == ""


def test_history_entry_from_dict_roundtrip():
    entry = _make_entry(note="initial")
    entry.note = "initial"
    restored = HistoryEntry.from_dict(entry.to_dict())
    assert restored.profile_name == entry.profile_name
    assert restored.variables == entry.variables
    assert restored.note == "initial"


def test_record_persists_to_disk(store_path: Path, store: HistoryStore):
    store.record(_make_entry())
    data = json.loads(store_path.read_text())
    assert len(data) == 1
    assert data[0]["profile_name"] == "base"


def test_entries_for_profile_filters_correctly(store: HistoryStore):
    store.record(_make_entry("alpha"))
    store.record(_make_entry("beta"))
    store.record(_make_entry("alpha"))
    result = store.entries_for_profile("alpha")
    assert len(result) == 2
    assert all(e.profile_name == "alpha" for e in result)


def test_all_entries_returns_everything(store: HistoryStore):
    store.record(_make_entry("a"))
    store.record(_make_entry("b"))
    assert len(store.all_entries()) == 2


def test_clear_profile_removes_entries(store: HistoryStore):
    store.record(_make_entry("x"))
    store.record(_make_entry("y"))
    removed = store.clear_profile("x")
    assert removed == 1
    assert len(store.entries_for_profile("x")) == 0


def test_clear_profile_no_match_returns_zero(store: HistoryStore):
    store.record(_make_entry("z"))
    removed = store.clear_profile("missing")
    assert removed == 0


def test_store_loads_existing_file(store_path: Path):
    entry = _make_entry()
    store_path.write_text(json.dumps([entry.to_dict()]))
    loaded = HistoryStore(store_path)
    assert len(loaded.all_entries()) == 1
    assert loaded.all_entries()[0].profile_name == "base"
