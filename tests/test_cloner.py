"""Tests for envchain.cloner."""

import pytest

from envchain.cloner import CloneError, CloneResult, clone_profile
from envchain.profile import Profile, ProfileStore
from envchain.validator import ValidationError


@pytest.fixture()
def store(tmp_path):
    s = ProfileStore(tmp_path / "profiles.json")
    s.add(
        Profile(
            name="base",
            context="local",
            variables={"API_KEY": "abc123", "DEBUG": "true"},
        )
    )
    return s


def test_clone_creates_new_profile(store):
    result = clone_profile(store, "base", "base_copy")
    assert isinstance(result, CloneResult)
    assert result.source_name == "base"
    assert result.target_name == "base_copy"
    assert result.variables_copied == 2


def test_cloned_profile_has_same_variables(store):
    clone_profile(store, "base", "base_copy")
    cloned = store.get("base_copy")
    assert cloned is not None
    assert cloned.variables == {"API_KEY": "abc123", "DEBUG": "true"}


def test_cloned_profile_inherits_context(store):
    clone_profile(store, "base", "base_copy")
    cloned = store.get("base_copy")
    assert cloned.context == "local"


def test_clone_with_context_override(store):
    clone_profile(store, "base", "base_prod", context="production")
    cloned = store.get("base_prod")
    assert cloned.context == "production"


def test_clone_missing_source_raises(store):
    with pytest.raises(CloneError, match="does not exist"):
        clone_profile(store, "nonexistent", "copy")


def test_clone_existing_target_raises(store):
    clone_profile(store, "base", "base_copy")
    with pytest.raises(CloneError, match="already exists"):
        clone_profile(store, "base", "base_copy")


def test_clone_overwrite_replaces_target(store):
    clone_profile(store, "base", "base_copy")
    # Modify original then overwrite the clone
    original = store.get("base")
    original.variables["NEW_VAR"] = "hello"
    store.add(original)  # update in store
    result = clone_profile(store, "base", "base_copy", overwrite=True)
    assert result.variables_copied == 3
    cloned = store.get("base_copy")
    assert cloned.variables.get("NEW_VAR") == "hello"


def test_clone_invalid_target_name_raises(store):
    with pytest.raises(ValidationError):
        clone_profile(store, "base", "")


def test_clone_result_summary(store):
    result = clone_profile(store, "base", "base_copy")
    assert "base" in result.summary
    assert "base_copy" in result.summary
    assert "2" in result.summary
