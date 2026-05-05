"""Tests for envchain.watchdog module."""

import json
import pytest
from pathlib import Path

from envchain.profile import Profile, ProfileStore
from envchain.snapshot import Snapshot, SnapshotStore
from envchain.watchdog import check_drift, check_all_drift, DriftReport, WatchdogError


@pytest.fixture
def tmp_profile_store(tmp_path):
    return ProfileStore(tmp_path / "profiles.json")


@pytest.fixture
def tmp_snapshot_store(tmp_path):
    return SnapshotStore(tmp_path / "snapshots.json")


def _add_profile(store, name, variables, context="local"):
    p = Profile(name=name, context=context, variables=variables)
    store.add(p)
    return p


def _add_snapshot(store, label, profiles):
    snap = Snapshot(label=label, profiles=profiles)
    store.add(snap)
    return snap


def test_drift_report_no_drift(tmp_profile_store, tmp_snapshot_store):
    p = _add_profile(tmp_profile_store, "base", {"KEY": "value"})
    _add_snapshot(tmp_snapshot_store, "v1", [p])
    report = check_drift("base", "v1", tmp_profile_store, tmp_snapshot_store)
    assert not report.drifted
    assert "No drift" in report.summary()


def test_drift_report_detects_added_key(tmp_profile_store, tmp_snapshot_store):
    old = Profile(name="base", context="local", variables={"KEY": "value"})
    _add_snapshot(tmp_snapshot_store, "v1", [old])
    _add_profile(tmp_profile_store, "base", {"KEY": "value", "NEW": "extra"})
    report = check_drift("base", "v1", tmp_profile_store, tmp_snapshot_store)
    assert report.drifted
    assert "Drift detected" in report.summary()


def test_drift_report_detects_changed_value(tmp_profile_store, tmp_snapshot_store):
    old = Profile(name="base", context="local", variables={"KEY": "old"})
    _add_snapshot(tmp_snapshot_store, "v1", [old])
    _add_profile(tmp_profile_store, "base", {"KEY": "new"})
    report = check_drift("base", "v1", tmp_profile_store, tmp_snapshot_store)
    assert report.drifted


def test_check_drift_missing_profile_raises(tmp_profile_store, tmp_snapshot_store):
    old = Profile(name="base", context="local", variables={"KEY": "v"})
    _add_snapshot(tmp_snapshot_store, "v1", [old])
    with pytest.raises(WatchdogError, match="Profile 'missing'"):
        check_drift("missing", "v1", tmp_profile_store, tmp_snapshot_store)


def test_check_drift_missing_snapshot_raises(tmp_profile_store, tmp_snapshot_store):
    _add_profile(tmp_profile_store, "base", {"KEY": "v"})
    with pytest.raises(WatchdogError, match="Snapshot 'nope'"):
        check_drift("base", "nope", tmp_profile_store, tmp_snapshot_store)


def test_check_all_drift_returns_reports(tmp_profile_store, tmp_snapshot_store):
    p1 = _add_profile(tmp_profile_store, "alpha", {"A": "1"})
    p2 = _add_profile(tmp_profile_store, "beta", {"B": "2"})
    _add_snapshot(tmp_snapshot_store, "v1", [p1, p2])
    reports = check_all_drift("v1", tmp_profile_store, tmp_snapshot_store)
    assert len(reports) == 2
    assert all(isinstance(r, DriftReport) for r in reports)


def test_check_all_drift_missing_snapshot_raises(tmp_profile_store, tmp_snapshot_store):
    with pytest.raises(WatchdogError, match="Snapshot 'ghost'"):
        check_all_drift("ghost", tmp_profile_store, tmp_snapshot_store)
