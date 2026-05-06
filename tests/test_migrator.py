"""Tests for envchain.migrator."""
import pytest

from envchain.profile import Profile, ProfileStore
from envchain.migrator import (
    MigrationError,
    MigrationResult,
    migrate_profile,
    migrate_all,
)


@pytest.fixture()
def store(tmp_path):
    s = ProfileStore(tmp_path / "profiles.json")
    s.add(Profile(name="dev", context="local", variables={"DB_HOST": "localhost", "DB_PORT": "5432"}))
    s.add(Profile(name="prod", context="production", variables={"DB_HOST": "prod.db", "API_KEY": "secret"}))
    s.add(Profile(name="staging", context="staging", variables={"DB_HOST": "stage.db", "DB_PORT": "5433"}))
    return s


def test_migrate_renames_key(store):
    result = migrate_profile(store, "dev", {"DB_HOST": "DATABASE_HOST"})
    assert result.has_changes
    assert result.renamed == {"DB_HOST": "DATABASE_HOST"}
    profile = store.get("dev")
    assert "DATABASE_HOST" in profile.variables
    assert "DB_HOST" not in profile.variables


def test_migrate_preserves_value(store):
    migrate_profile(store, "dev", {"DB_HOST": "DATABASE_HOST"})
    profile = store.get("dev")
    assert profile.variables["DATABASE_HOST"] == "localhost"


def test_migrate_skips_missing_key(store):
    result = migrate_profile(store, "dev", {"NONEXISTENT": "NEW_KEY"})
    assert not result.has_changes
    assert "NONEXISTENT" in result.skipped


def test_migrate_raises_on_existing_new_key_without_overwrite(store):
    store.add(Profile(name="dev", context="local",
                      variables={"DB_HOST": "localhost", "DB_PORT": "5432", "DATABASE_HOST": "other"}))
    with pytest.raises(MigrationError, match="already exists"):
        migrate_profile(store, "dev", {"DB_HOST": "DATABASE_HOST"})


def test_migrate_overwrites_when_flag_set(store):
    store.add(Profile(name="dev", context="local",
                      variables={"DB_HOST": "localhost", "DB_PORT": "5432", "DATABASE_HOST": "old"}))
    result = migrate_profile(store, "dev", {"DB_HOST": "DATABASE_HOST"}, overwrite=True)
    assert result.has_changes
    assert store.get("dev").variables["DATABASE_HOST"] == "localhost"


def test_migrate_missing_profile_raises(store):
    with pytest.raises(MigrationError, match="not found"):
        migrate_profile(store, "ghost", {"A": "B"})


def test_migration_result_summary_no_changes(store):
    result = migrate_profile(store, "dev", {"MISSING": "X"})
    assert "no changes" in result.summary()


def test_migration_result_summary_with_changes(store):
    result = migrate_profile(store, "dev", {"DB_HOST": "DATABASE_HOST"})
    assert "DB_HOST -> DATABASE_HOST" in result.summary()


def test_migrate_all_applies_to_every_profile(store):
    results = migrate_all(store, {"DB_HOST": "DATABASE_HOST"})
    changed = [r for r in results if r.has_changes]
    assert len(changed) == 3


def test_migrate_all_filters_by_context(store):
    results = migrate_all(store, {"DB_HOST": "DATABASE_HOST"}, context="local")
    assert len(results) == 1
    assert results[0].profile_name == "dev"


def test_migrate_all_returns_results_for_all_profiles(store):
    results = migrate_all(store, {"NONEXISTENT": "X"})
    assert len(results) == 3
    assert all(not r.has_changes for r in results)
