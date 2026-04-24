"""Tests for the ProfileResolver."""

import pytest
from envchain.profile import Profile, ProfileStore
from envchain.resolver import ProfileResolver, ChainResolutionError


@pytest.fixture
def store(tmp_path):
    s = ProfileStore(str(tmp_path / "profiles.json"))
    s.add_profile(Profile(name="base", context="local", variables={"APP": "myapp", "DEBUG": "true"}))
    s.add_profile(Profile(name="db", context="local", variables={"DB_HOST": "localhost", "DB_PORT": "5432"}))
    s.add_profile(Profile(name="override", context="local", variables={"DEBUG": "false", "LOG_LEVEL": "info"}))
    s.add_profile(Profile(name="prod_base", context="production", variables={"APP": "myapp", "DEBUG": "false"}))
    return s


@pytest.fixture
def resolver(store):
    return ProfileResolver(store)


def test_resolve_single_profile(resolver):
    result = resolver.resolve_single("base", context="local")
    assert result == {"APP": "myapp", "DEBUG": "true"}


def test_resolve_chain_merges_variables(resolver):
    result = resolver.resolve(["base", "db"], context="local")
    assert result["APP"] == "myapp"
    assert result["DB_HOST"] == "localhost"
    assert result["DB_PORT"] == "5432"


def test_later_profile_overrides_earlier(resolver):
    result = resolver.resolve(["base", "override"], context="local")
    assert result["DEBUG"] == "false"
    assert result["LOG_LEVEL"] == "info"
    assert result["APP"] == "myapp"


def test_resolve_missing_profile_raises(resolver):
    with pytest.raises(ChainResolutionError, match="nonexistent"):
        resolver.resolve(["base", "nonexistent"], context="local")


def test_resolve_wrong_context_raises(resolver):
    with pytest.raises(ChainResolutionError):
        resolver.resolve_single("base", context="production")


def test_list_chain_returns_profiles(resolver):
    profiles = resolver.list_chain(["base", "db"], context="local")
    assert len(profiles) == 2
    assert profiles[0].name == "base"
    assert profiles[1].name == "db"


def test_resolve_empty_chain_returns_empty(resolver):
    result = resolver.resolve([], context="local")
    assert result == {}


def test_resolve_three_profiles_full_merge(resolver):
    result = resolver.resolve(["base", "db", "override"], context="local")
    assert result["APP"] == "myapp"
    assert result["DEBUG"] == "false"
    assert result["DB_HOST"] == "localhost"
    assert result["LOG_LEVEL"] == "info"
