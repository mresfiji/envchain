"""Tests for envchain.archiver."""

import json
from pathlib import Path

import pytest

from envchain.archiver import ArchiveError, archive_profiles, restore_profiles
from envchain.profile import Profile, ProfileStore


@pytest.fixture()
def store(tmp_path: Path) -> ProfileStore:
    s = ProfileStore(tmp_path / "profiles.json")
    s.add(Profile(name="dev", context="local", variables={"DB_URL": "localhost", "DEBUG": "1"}))
    s.add(Profile(name="staging", context="staging", variables={"DB_URL": "staging.db", "DEBUG": "0"}))
    return s


@pytest.fixture()
def bundle_path(tmp_path: Path) -> Path:
    return tmp_path / "bundle.json"


def test_archive_writes_bundle(store, bundle_path):
    result = archive_profiles(store, ["dev", "staging"], bundle_path)
    assert result.archived == ["dev", "staging"]
    assert result.skipped == []
    assert bundle_path.exists()


def test_archive_bundle_content_is_valid_json(store, bundle_path):
    archive_profiles(store, ["dev"], bundle_path)
    data = json.loads(bundle_path.read_text())
    assert "dev" in data
    assert data["dev"]["variables"]["DB_URL"] == "localhost"


def test_archive_skips_missing_profiles(store, bundle_path):
    result = archive_profiles(store, ["dev", "ghost"], bundle_path)
    assert "ghost" in result.skipped
    assert "dev" in result.archived


def test_archive_raises_if_dest_exists(store, bundle_path):
    bundle_path.write_text("{}")
    with pytest.raises(ArchiveError, match="already exists"):
        archive_profiles(store, ["dev"], bundle_path)


def test_archive_overwrite_flag(store, bundle_path):
    bundle_path.write_text("{}")
    result = archive_profiles(store, ["dev"], bundle_path, overwrite=True)
    assert result.archived == ["dev"]


def test_archive_summary_no_skipped(store, bundle_path):
    result = archive_profiles(store, ["dev"], bundle_path)
    assert "1 profile" in result.summary()
    assert "skipped" not in result.summary()


def test_archive_summary_with_skipped(store, bundle_path):
    result = archive_profiles(store, ["dev", "missing"], bundle_path)
    assert "skipped" in result.summary()


def test_restore_loads_profiles(store, bundle_path, tmp_path):
    archive_profiles(store, ["dev", "staging"], bundle_path)
    empty_store = ProfileStore(tmp_path / "restored.json")
    restored = restore_profiles(empty_store, bundle_path)
    assert set(restored) == {"dev", "staging"}
    assert empty_store.get("dev") is not None


def test_restore_raises_on_missing_file(tmp_path):
    empty_store = ProfileStore(tmp_path / "profiles.json")
    with pytest.raises(ArchiveError, match="not found"):
        restore_profiles(empty_store, tmp_path / "no_such_file.json")


def test_restore_raises_on_invalid_json(store, bundle_path, tmp_path):
    bundle_path.write_text("not json")
    empty_store = ProfileStore(tmp_path / "profiles.json")
    with pytest.raises(ArchiveError, match="Invalid archive format"):
        restore_profiles(empty_store, bundle_path)


def test_restore_raises_on_duplicate_without_overwrite(store, bundle_path):
    archive_profiles(store, ["dev"], bundle_path)
    with pytest.raises(ArchiveError, match="already exists"):
        restore_profiles(store, bundle_path)


def test_restore_overwrite_replaces_profile(store, bundle_path, tmp_path):
    archive_profiles(store, ["dev"], bundle_path)
    restored = restore_profiles(store, bundle_path, overwrite=True)
    assert "dev" in restored
