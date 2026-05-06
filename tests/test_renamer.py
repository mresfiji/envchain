"""Tests for envchain.renamer."""

import pytest

from envchain.profile import Profile, ProfileStore
from envchain.renamer import RenameError, RenameResult, rename_profile


@pytest.fixture()
def store(tmp_path):
    s = ProfileStore(tmp_path / "profiles.json")
    s.add_profile(Profile(name="base", context="local", variables={"FOO": "bar", "BAZ": "qux"}))
    s.add_profile(Profile(name="other", context="local", variables={"X": "1"}))
    return s


def test_rename_creates_new_profile(store):
    rename_profile(store, "base", "renamed", "local")
    result = store.get_profile("renamed", "local")
    assert result is not None
    assert result.name == "renamed"


def test_rename_removes_old_profile(store):
    rename_profile(store, "base", "renamed", "local")
    assert store.get_profile("base", "local") is None


def test_rename_preserves_variables(store):
    rename_profile(store, "base", "renamed", "local")
    result = store.get_profile("renamed", "local")
    assert result.variables == {"FOO": "bar", "BAZ": "qux"}


def test_rename_preserves_context(store):
    rename_profile(store, "base", "renamed", "local")
    result = store.get_profile("renamed", "local")
    assert result.context == "local"


def test_rename_returns_result(store):
    result = rename_profile(store, "base", "renamed", "local")
    assert isinstance(result, RenameResult)
    assert result.old_name == "base"
    assert result.new_name == "renamed"
    assert result.context == "local"
    assert result.variables_count == 2


def test_rename_result_summary(store):
    result = rename_profile(store, "base", "renamed", "local")
    summary = result.summary()
    assert "base" in summary
    assert "renamed" in summary
    assert "local" in summary


def test_rename_missing_source_raises(store):
    with pytest.raises(RenameError, match="not found"):
        rename_profile(store, "nonexistent", "renamed", "local")


def test_rename_target_already_exists_raises(store):
    with pytest.raises(RenameError, match="already exists"):
        rename_profile(store, "base", "other", "local")


def test_rename_does_not_affect_other_profiles(store):
    rename_profile(store, "base", "renamed", "local")
    other = store.get_profile("other", "local")
    assert other is not None
    assert other.variables == {"X": "1"}
