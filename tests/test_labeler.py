"""Tests for envchain.labeler."""
import json
import pytest
from pathlib import Path
from envchain.labeler import LabelError, LabelIndex


@pytest.fixture
def index() -> LabelIndex:
    return LabelIndex()


def test_add_and_labels_for_profile(index):
    index.add("dev", "experimental")
    index.add("dev", "internal")
    assert index.labels_for_profile("dev") == ["experimental", "internal"]


def test_labels_for_profile_unknown_returns_empty(index):
    assert index.labels_for_profile("ghost") == []


def test_profiles_for_label(index):
    index.add("dev", "ci")
    index.add("staging", "ci")
    index.add("prod", "stable")
    assert index.profiles_for_label("ci") == ["dev", "staging"]


def test_profiles_for_label_unknown_returns_empty(index):
    assert index.profiles_for_label("nope") == []


def test_all_labels(index):
    index.add("dev", "ci")
    index.add("prod", "stable")
    index.add("dev", "stable")
    assert index.all_labels() == ["ci", "stable"]


def test_remove_label(index):
    index.add("dev", "ci")
    index.remove("dev", "ci")
    assert index.labels_for_profile("dev") == []


def test_remove_last_label_cleans_up_profile(index):
    index.add("dev", "only")
    index.remove("dev", "only")
    assert "dev" not in index._data


def test_remove_missing_label_raises(index):
    with pytest.raises(LabelError, match="not found"):
        index.remove("dev", "missing")


def test_add_empty_label_raises(index):
    with pytest.raises(LabelError, match="empty"):
        index.add("dev", "   ")


def test_to_dict_and_from_dict_roundtrip(index):
    index.add("dev", "ci")
    index.add("prod", "stable")
    restored = LabelIndex.from_dict(index.to_dict())
    assert restored.labels_for_profile("dev") == ["ci"]
    assert restored.labels_for_profile("prod") == ["stable"]


def test_save_and_load(tmp_path):
    path = tmp_path / "labels.json"
    idx = LabelIndex()
    idx.add("dev", "ci")
    idx.save(path)
    loaded = LabelIndex.load(path)
    assert loaded.labels_for_profile("dev") == ["ci"]


def test_load_missing_file_returns_empty(tmp_path):
    idx = LabelIndex.load(tmp_path / "nonexistent.json")
    assert idx.all_labels() == []


def test_save_writes_valid_json(tmp_path):
    path = tmp_path / "labels.json"
    idx = LabelIndex()
    idx.add("dev", "alpha")
    idx.save(path)
    data = json.loads(path.read_text())
    assert data == {"dev": ["alpha"]}
