"""Tests for envchain.expirator."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envchain.expirator import ExpirationError, ExpiryEntry, ExpiryStore

PAST = datetime(2000, 1, 1, tzinfo=timezone.utc)
FUTURE = datetime(2099, 1, 1, tzinfo=timezone.utc)


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "expiry.json"


@pytest.fixture
def store(store_path: Path) -> ExpiryStore:
    return ExpiryStore(store_path)


def _make_entry(profile="prod", variable="API_KEY", expires_at=FUTURE, note=""):
    return ExpiryEntry(profile=profile, variable=variable, expires_at=expires_at, note=note)


def test_expiry_entry_to_dict():
    entry = _make_entry()
    d = entry.to_dict()
    assert d["profile"] == "prod"
    assert d["variable"] == "API_KEY"
    assert "expires_at" in d


def test_expiry_entry_from_dict_roundtrip():
    entry = _make_entry(note="rotate soon")
    restored = ExpiryEntry.from_dict(entry.to_dict())
    assert restored.profile == entry.profile
    assert restored.variable == entry.variable
    assert restored.note == entry.note


def test_is_expired_past():
    entry = _make_entry(expires_at=PAST)
    assert entry.is_expired()


def test_is_expired_future():
    entry = _make_entry(expires_at=FUTURE)
    assert not entry.is_expired()


def test_is_expired_uses_provided_now():
    entry = _make_entry(expires_at=datetime(2050, 6, 1, tzinfo=timezone.utc))
    before = datetime(2050, 5, 31, tzinfo=timezone.utc)
    after = datetime(2050, 6, 2, tzinfo=timezone.utc)
    assert not entry.is_expired(now=before)
    assert entry.is_expired(now=after)


def test_set_and_get(store: ExpiryStore):
    entry = _make_entry()
    store.set(entry)
    result = store.get("prod", "API_KEY")
    assert result is not None
    assert result.variable == "API_KEY"


def test_get_missing_returns_none(store: ExpiryStore):
    assert store.get("prod", "MISSING") is None


def test_remove_entry(store: ExpiryStore):
    store.set(_make_entry())
    store.remove("prod", "API_KEY")
    assert store.get("prod", "API_KEY") is None


def test_remove_missing_raises(store: ExpiryStore):
    with pytest.raises(ExpirationError):
        store.remove("prod", "NONEXISTENT")


def test_expired_entries(store: ExpiryStore):
    store.set(_make_entry(variable="OLD", expires_at=PAST))
    store.set(_make_entry(variable="NEW", expires_at=FUTURE))
    expired = store.expired_entries()
    assert len(expired) == 1
    assert expired[0].variable == "OLD"


def test_all_entries(store: ExpiryStore):
    store.set(_make_entry(variable="A"))
    store.set(_make_entry(variable="B"))
    assert len(store.all_entries()) == 2


def test_persistence(store_path: Path):
    s1 = ExpiryStore(store_path)
    s1.set(_make_entry(note="persisted"))
    s2 = ExpiryStore(store_path)
    result = s2.get("prod", "API_KEY")
    assert result is not None
    assert result.note == "persisted"
