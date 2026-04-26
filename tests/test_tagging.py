"""Tests for envchain.tagging module."""
import pytest

from envchain.tagging import TagError, TagIndex


@pytest.fixture
def index() -> TagIndex:
    idx = TagIndex()
    idx.add("production", "prod-db")
    idx.add("production", "prod-api")
    idx.add("staging", "staging-db")
    idx.add("staging", "prod-db")
    return idx


def test_add_and_profiles_for_tag(index):
    assert index.profiles_for_tag("production") == ["prod-api", "prod-db"]


def test_profiles_for_tag_unknown_returns_empty(index):
    assert index.profiles_for_tag("nonexistent") == []


def test_tags_for_profile(index):
    assert index.tags_for_profile("prod-db") == ["production", "staging"]


def test_tags_for_profile_unknown_returns_empty(index):
    assert index.tags_for_profile("ghost") == []


def test_all_tags(index):
    assert index.all_tags() == ["production", "staging"]


def test_remove_tag(index):
    index.remove("staging", "prod-db")
    assert "prod-db" not in index.profiles_for_tag("staging")


def test_remove_last_profile_deletes_tag(index):
    index.remove("staging", "staging-db")
    index.remove("staging", "prod-db")
    assert "staging" not in index.all_tags()


def test_remove_nonexistent_raises(index):
    with pytest.raises(TagError, match="does not have tag"):
        index.remove("production", "ghost-profile")


def test_invalid_tag_raises():
    idx = TagIndex()
    with pytest.raises(TagError, match="Invalid tag"):
        idx.add("bad tag!", "some-profile")


def test_empty_tag_raises():
    idx = TagIndex()
    with pytest.raises(TagError, match="must not be empty"):
        idx.add("", "some-profile")


def test_tag_normalized_to_lowercase():
    idx = TagIndex()
    idx.add("Production", "my-profile")
    assert "my-profile" in idx.profiles_for_tag("production")


def test_roundtrip_serialization(index):
    data = index.to_dict()
    restored = TagIndex.from_dict(data)
    assert restored.all_tags() == index.all_tags()
    assert restored.profiles_for_tag("production") == index.profiles_for_tag("production")
