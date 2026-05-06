"""Tests for envchain.grouper."""
import pytest
from envchain.grouper import GroupIndex, GroupError


@pytest.fixture()
def index() -> GroupIndex:
    return GroupIndex()


def test_add_and_profiles_for_group(index):
    index.add("backend", "prod-api")
    index.add("backend", "staging-api")
    assert index.profiles_for_group("backend") == ["prod-api", "staging-api"]


def test_profiles_for_group_unknown_returns_empty(index):
    assert index.profiles_for_group("nonexistent") == []


def test_groups_for_profile(index):
    index.add("backend", "api")
    index.add("infra", "api")
    groups = index.groups_for_profile("api")
    assert "backend" in groups
    assert "infra" in groups


def test_groups_for_profile_unknown_returns_empty(index):
    assert index.groups_for_profile("ghost") == []


def test_add_duplicate_is_idempotent(index):
    index.add("g", "p")
    index.add("g", "p")
    assert index.profiles_for_group("g") == ["p"]


def test_remove_profile_from_group(index):
    index.add("g", "p1")
    index.add("g", "p2")
    index.remove("g", "p1")
    assert index.profiles_for_group("g") == ["p2"]


def test_remove_last_member_deletes_group(index):
    index.add("solo", "only")
    index.remove("solo", "only")
    assert "solo" not in index.all_groups()


def test_remove_missing_group_raises(index):
    with pytest.raises(GroupError, match="does not exist"):
        index.remove("ghost", "p")


def test_remove_missing_profile_raises(index):
    index.add("g", "p")
    with pytest.raises(GroupError, match="not in group"):
        index.remove("g", "missing")


def test_all_groups(index):
    index.add("a", "x")
    index.add("b", "y")
    assert set(index.all_groups()) == {"a", "b"}


def test_roundtrip_serialization(index):
    index.add("g1", "p1")
    index.add("g1", "p2")
    index.add("g2", "p3")
    restored = GroupIndex.from_dict(index.to_dict())
    assert restored.profiles_for_group("g1") == ["p1", "p2"]
    assert restored.profiles_for_group("g2") == ["p3"]


def test_empty_group_name_raises(index):
    with pytest.raises(GroupError, match="Group name"):
        index.add("", "p")


def test_empty_profile_name_raises(index):
    with pytest.raises(GroupError, match="Profile name"):
        index.add("g", "")
