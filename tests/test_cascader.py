"""Tests for envchain.cascader."""
import pytest

from envchain.cascader import CascadeError, CascadeResult, cascade_profiles
from envchain.profile import Profile, ProfileStore


@pytest.fixture()
def store(tmp_path):
    s = ProfileStore(tmp_path / "profiles.json")
    s.add(Profile(name="base", context="local", variables={"HOST": "localhost", "PORT": "5432"}))
    s.add(Profile(name="staging", context="staging", variables={"HOST": "staging.example.com", "DEBUG": "false"}))
    s.add(Profile(name="overrides", context="local", variables={"PORT": "9999", "DEBUG": "true"}))
    return s


def test_cascade_single_profile(store):
    result = cascade_profiles(["base"], store)
    assert result.merged_variables == {"HOST": "localhost", "PORT": "5432"}
    assert result.override_map["HOST"] == "base"


def test_cascade_merges_two_profiles(store):
    result = cascade_profiles(["base", "staging"], store)
    assert result.merged_variables["HOST"] == "staging.example.com"
    assert result.merged_variables["PORT"] == "5432"
    assert result.merged_variables["DEBUG"] == "false"
    assert result.override_map["HOST"] == "staging"


def test_cascade_later_overrides_earlier(store):
    result = cascade_profiles(["base", "staging", "overrides"], store)
    assert result.merged_variables["PORT"] == "9999"
    assert result.merged_variables["DEBUG"] == "true"
    assert result.override_map["PORT"] == "overrides"
    assert result.override_map["DEBUG"] == "overrides"


def test_cascade_with_base_variables(store):
    result = cascade_profiles(["base"], store, base_variables={"EXTRA": "yes"})
    assert result.merged_variables["EXTRA"] == "yes"
    assert result.override_map["EXTRA"] == "<base>"


def test_cascade_base_variable_overridden_by_profile(store):
    result = cascade_profiles(["base"], store, base_variables={"PORT": "0000"})
    assert result.merged_variables["PORT"] == "5432"
    assert result.override_map["PORT"] == "base"


def test_cascade_empty_list_raises(store):
    with pytest.raises(CascadeError, match="At least one profile"):
        cascade_profiles([], store)


def test_cascade_missing_profile_raises(store):
    with pytest.raises(CascadeError, match="Profile not found"):
        cascade_profiles(["base", "nonexistent"], store)


def test_cascade_result_summary(store):
    result = cascade_profiles(["base", "staging"], store)
    summary = result.summary()
    assert "base -> staging" in summary
    assert "2 profiles" in summary


def test_cascade_profile_names_preserved(store):
    result = cascade_profiles(["base", "overrides"], store)
    assert result.profile_names == ["base", "overrides"]
