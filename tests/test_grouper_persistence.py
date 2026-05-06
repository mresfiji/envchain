"""Persistence tests for envchain.grouper (load/save round-trip)."""
import json
from pathlib import Path

import pytest

from envchain.grouper import GroupIndex, load_index, save_index


@pytest.fixture()
def tmp_index(tmp_path) -> Path:
    return tmp_path / "groups.json"


def test_load_returns_empty_index_when_file_missing(tmp_index):
    index = load_index(tmp_index)
    assert index.all_groups() == []


def test_save_creates_file(tmp_index):
    index = GroupIndex()
    index.add("g", "p")
    save_index(index, tmp_index)
    assert tmp_index.exists()


def test_save_and_load_roundtrip(tmp_index):
    index = GroupIndex()
    index.add("frontend", "app-prod")
    index.add("frontend", "app-staging")
    index.add("backend", "api-prod")
    save_index(index, tmp_index)

    restored = load_index(tmp_index)
    assert set(restored.profiles_for_group("frontend")) == {"app-prod", "app-staging"}
    assert restored.profiles_for_group("backend") == ["api-prod"]


def test_save_writes_valid_json(tmp_index):
    index = GroupIndex()
    index.add("g", "p")
    save_index(index, tmp_index)
    data = json.loads(tmp_index.read_text())
    assert isinstance(data, dict)
    assert data["g"] == ["p"]


def test_load_existing_file(tmp_index):
    tmp_index.write_text(json.dumps({"ops": ["deploy", "rollback"]}))
    index = load_index(tmp_index)
    assert index.profiles_for_group("ops") == ["deploy", "rollback"]
