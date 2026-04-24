"""Tests for envchain.audit module."""

import json
import pytest
from pathlib import Path

from envchain.audit import AuditEntry, AuditLog


@pytest.fixture
def log_path(tmp_path: Path) -> Path:
    return tmp_path / "audit.json"


@pytest.fixture
def audit_log(log_path: Path) -> AuditLog:
    return AuditLog(log_path)


def test_record_creates_entry(audit_log: AuditLog) -> None:
    entry = audit_log.record("read", "base", "local")
    assert entry.action == "read"
    assert entry.profile_name == "base"
    assert entry.context == "local"
    assert entry.details is None
    assert entry.timestamp


def test_record_with_details(audit_log: AuditLog) -> None:
    entry = audit_log.record("write", "secrets", "production", details="added DB_URL")
    assert entry.details == "added DB_URL"


def test_entries_returns_all(audit_log: AuditLog) -> None:
    audit_log.record("read", "base", "local")
    audit_log.record("write", "base", "staging")
    assert len(audit_log.entries()) == 2


def test_entries_for_profile_filters(audit_log: AuditLog) -> None:
    audit_log.record("read", "base", "local")
    audit_log.record("read", "secrets", "local")
    audit_log.record("write", "base", "production")
    base_entries = audit_log.entries_for_profile("base")
    assert len(base_entries) == 2
    assert all(e.profile_name == "base" for e in base_entries)


def test_entries_persisted_to_disk(log_path: Path) -> None:
    log1 = AuditLog(log_path)
    log1.record("read", "base", "local")

    log2 = AuditLog(log_path)
    assert len(log2.entries()) == 1
    assert log2.entries()[0].action == "read"


def test_log_file_is_valid_json(log_path: Path) -> None:
    audit_log = AuditLog(log_path)
    audit_log.record("delete", "old-profile", "staging")
    with open(log_path, "r") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert data[0]["action"] == "delete"


def test_clear_removes_all_entries(audit_log: AuditLog) -> None:
    audit_log.record("read", "base", "local")
    audit_log.record("write", "base", "local")
    audit_log.clear()
    assert audit_log.entries() == []


def test_audit_entry_roundtrip() -> None:
    entry = AuditEntry(action="read", profile_name="base", context="local", details="test")
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.action == entry.action
    assert restored.profile_name == entry.profile_name
    assert restored.context == entry.context
    assert restored.details == entry.details
    assert restored.timestamp == entry.timestamp
