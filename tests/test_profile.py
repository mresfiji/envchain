"""Tests for Profile model and ProfileStore."""

import json
import pytest
from pathlib import Path
from envchain.profile import Profile, ProfileStore


@pytest.fixture
def tmp_store(tmp_path):
    store_file = tmp_path / "profiles.json"
    return ProfileStore(store_path=store_file)


def test_profile_to_dict():
    p = Profile(name="dev", context="local", vars={"DEBUG": "1"}, description="Dev env")
    d = p.to_dict()
    assert d["name"] == "dev"
    assert d["context"] == "local"
    assert d["vars"] == {"DEBUG": "1"}


def test_profile_from_dict():
    data = {"name": "prod", "context": "production", "vars": {"API_KEY": "abc"}, "description": ""}
    p = Profile.from_dict(data)
    assert p.name == "prod"
    assert p.context == "production"
    assert p.vars["API_KEY"] == "abc"


def test_add_and_get_profile(tmp_store):
    p = Profile(name="staging-api", context="staging", vars={"HOST": "staging.example.com"})
    tmp_store.add(p)
    retrieved = tmp_store.get("staging-api")
    assert retrieved is not None
    assert retrieved.vars["HOST"] == "staging.example.com"


def test_add_invalid_context_raises(tmp_store):
    p = Profile(name="bad", context="development")
    with pytest.raises(ValueError, match="Invalid context"):
        tmp_store.add(p)


def test_remove_profile(tmp_store):
    p = Profile(name="temp", context="local")
    tmp_store.add(p)
    assert tmp_store.remove("temp") is True
    assert tmp_store.get("temp") is None


def test_remove_nonexistent_returns_false(tmp_store):
    assert tmp_store.remove("ghost") is False


def test_list_all(tmp_store):
    tmp_store.add(Profile(name="a", context="local"))
    tmp_store.add(Profile(name="b", context="staging"))
    assert len(tmp_store.list_all()) == 2


def test_list_by_context(tmp_store):
    tmp_store.add(Profile(name="a", context="local"))
    tmp_store.add(Profile(name="b", context="staging"))
    tmp_store.add(Profile(name="c", context="local"))
    local = tmp_store.list_by_context("local")
    assert len(local) == 2
    assert all(p.context == "local" for p in local)


def test_persistence(tmp_path):
    store_file = tmp_path / "profiles.json"
    store1 = ProfileStore(store_path=store_file)
    store1.add(Profile(name="persist", context="production", vars={"KEY": "val"}))

    store2 = ProfileStore(store_path=store_file)
    p = store2.get("persist")
    assert p is not None
    assert p.vars["KEY"] == "val"
