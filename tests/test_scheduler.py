"""Tests for envchain.scheduler."""

import pytest
from pathlib import Path
from envchain.scheduler import ScheduledExport, ScheduleStore, SchedulerError


@pytest.fixture
def store_path(tmp_path):
    return tmp_path / "schedules.json"


@pytest.fixture
def store(store_path):
    return ScheduleStore(store_path)


def _make_schedule(label="nightly", profiles=None, fmt="dotenv", output="/tmp/out.env"):
    return ScheduledExport(
        profile_names=profiles or ["base", "prod"],
        output_path=output,
        format=fmt,
        label=label,
    )


def test_add_and_get_schedule(store):
    s = _make_schedule()
    store.add(s)
    result = store.get("nightly")
    assert result is not None
    assert result.label == "nightly"
    assert result.profile_names == ["base", "prod"]


def test_add_duplicate_label_raises(store):
    store.add(_make_schedule())
    with pytest.raises(SchedulerError, match="already exists"):
        store.add(_make_schedule())


def test_add_invalid_format_raises(store):
    with pytest.raises(SchedulerError, match="Unsupported format"):
        store.add(_make_schedule(fmt="yaml"))


def test_remove_schedule(store):
    store.add(_make_schedule())
    store.remove("nightly")
    assert store.get("nightly") is None


def test_remove_nonexistent_raises(store):
    with pytest.raises(SchedulerError, match="No schedule found"):
        store.remove("ghost")


def test_all_returns_all_schedules(store):
    store.add(_make_schedule("a", output="/tmp/a.env"))
    store.add(_make_schedule("b", output="/tmp/b.env"))
    assert len(store.all()) == 2


def test_active_filters_inactive(store):
    s1 = _make_schedule("active_one", output="/tmp/a.env")
    s2 = _make_schedule("inactive_one", output="/tmp/b.env")
    s2.active = False
    store.add(s1)
    store.add(s2)
    active = store.active()
    assert len(active) == 1
    assert active[0].label == "active_one"


def test_persistence_across_instances(store_path):
    s = ScheduleStore(store_path)
    s.add(_make_schedule())
    s2 = ScheduleStore(store_path)
    assert s2.get("nightly") is not None


def test_to_dict_and_from_dict():
    s = _make_schedule()
    d = s.to_dict()
    assert d["label"] == "nightly"
    restored = ScheduledExport.from_dict(d)
    assert restored.format == "dotenv"
    assert restored.active is True
