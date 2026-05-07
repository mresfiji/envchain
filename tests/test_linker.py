"""Tests for envchain.linker."""
import pytest
from pathlib import Path
from envchain.linker import LinkEntry, LinkStore, LinkError


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "links.json"


@pytest.fixture
def store(store_path: Path) -> LinkStore:
    return LinkStore(store_path)


def test_link_entry_to_dict():
    entry = LinkEntry(source="dev", target="base", note="inherits base")
    d = entry.to_dict()
    assert d == {"source": "dev", "target": "base", "note": "inherits base"}


def test_link_entry_from_dict_roundtrip():
    original = LinkEntry(source="staging", target="dev", note=None)
    restored = LinkEntry.from_dict(original.to_dict())
    assert restored.source == original.source
    assert restored.target == original.target
    assert restored.note is None


def test_link_creates_entry(store: LinkStore):
    entry = store.link("dev", "base")
    assert entry.source == "dev"
    assert entry.target == "base"


def test_link_persists(store_path: Path):
    s1 = LinkStore(store_path)
    s1.link("dev", "base", note="test note")
    s2 = LinkStore(store_path)
    entry = s2.get("dev")
    assert entry is not None
    assert entry.target == "base"
    assert entry.note == "test note"


def test_link_self_raises(store: LinkStore):
    with pytest.raises(LinkError, match="itself"):
        store.link("dev", "dev")


def test_link_duplicate_raises(store: LinkStore):
    store.link("dev", "base")
    with pytest.raises(LinkError, match="already has a link"):
        store.link("dev", "other")


def test_unlink_removes_entry(store: LinkStore):
    store.link("dev", "base")
    store.unlink("dev")
    assert store.get("dev") is None


def test_unlink_missing_raises(store: LinkStore):
    with pytest.raises(LinkError, match="No link found"):
        store.unlink("nonexistent")


def test_all_entries(store: LinkStore):
    store.link("dev", "base")
    store.link("staging", "dev")
    entries = store.all_entries()
    assert len(entries) == 2


def test_targets_for_chain(store: LinkStore):
    store.link("prod", "staging")
    store.link("staging", "dev")
    chain = store.targets_for("prod")
    assert chain == ["staging", "dev"]


def test_targets_for_no_link(store: LinkStore):
    assert store.targets_for("orphan") == []


def test_targets_for_cycle_safe(store: LinkStore):
    # manually inject a cycle
    store._entries["a"] = __import__("envchain.linker", fromlist=["LinkEntry"]).LinkEntry(source="a", target="b")
    store._entries["b"] = __import__("envchain.linker", fromlist=["LinkEntry"]).LinkEntry(source="b", target="a")
    result = store.targets_for("a")
    assert len(result) <= 2  # must not loop forever
