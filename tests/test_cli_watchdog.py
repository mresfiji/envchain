"""Tests for envchain.cli_watchdog CLI commands."""

import json
import pytest
from click.testing import CliRunner
from pathlib import Path

from envchain.cli_watchdog import cli
from envchain.profile import Profile, ProfileStore
from envchain.snapshot import Snapshot, SnapshotStore


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_paths(tmp_path):
    env_dir = tmp_path / ".envchain"
    env_dir.mkdir()
    profile_store = ProfileStore(env_dir / "profiles.json")
    snapshot_store = SnapshotStore(env_dir / "snapshots.json")
    return env_dir, profile_store, snapshot_store


def test_check_no_drift(runner, env_paths):
    env_dir, ps, ss = env_paths
    p = Profile(name="web", context="local", variables={"PORT": "8080"})
    ps.add(p)
    ss.add(Snapshot(label="v1", profiles=[p]))
    result = runner.invoke(cli, ["check", "web", "v1", "--env-dir", str(env_dir)])
    assert result.exit_code == 0
    assert "No drift" in result.output


def test_check_drift_detected(runner, env_paths):
    env_dir, ps, ss = env_paths
    old = Profile(name="web", context="local", variables={"PORT": "8080"})
    ss.add(Snapshot(label="v1", profiles=[old]))
    new = Profile(name="web", context="local", variables={"PORT": "9090"})
    ps.add(new)
    result = runner.invoke(cli, ["check", "web", "v1", "--env-dir", str(env_dir)])
    assert result.exit_code == 0
    assert "Drift detected" in result.output


def test_check_fail_on_drift_exits_1(runner, env_paths):
    env_dir, ps, ss = env_paths
    old = Profile(name="web", context="local", variables={"PORT": "8080"})
    ss.add(Snapshot(label="v1", profiles=[old]))
    ps.add(Profile(name="web", context="local", variables={"PORT": "9090"}))
    result = runner.invoke(
        cli, ["check", "web", "v1", "--env-dir", str(env_dir), "--fail-on-drift"]
    )
    assert result.exit_code == 1


def test_check_missing_profile_shows_error(runner, env_paths):
    env_dir, ps, ss = env_paths
    old = Profile(name="web", context="local", variables={"PORT": "8080"})
    ss.add(Snapshot(label="v1", profiles=[old]))
    result = runner.invoke(cli, ["check", "ghost", "v1", "--env-dir", str(env_dir)])
    assert result.exit_code != 0
    assert "ghost" in result.output


def test_check_all_no_drift(runner, env_paths):
    env_dir, ps, ss = env_paths
    p1 = Profile(name="alpha", context="local", variables={"A": "1"})
    p2 = Profile(name="beta", context="local", variables={"B": "2"})
    ps.add(p1)
    ps.add(p2)
    ss.add(Snapshot(label="v1", profiles=[p1, p2]))
    result = runner.invoke(cli, ["check-all", "v1", "--env-dir", str(env_dir)])
    assert result.exit_code == 0
    assert "No drift" in result.output


def test_check_all_missing_snapshot_error(runner, env_paths):
    env_dir, ps, ss = env_paths
    result = runner.invoke(cli, ["check-all", "nope", "--env-dir", str(env_dir)])
    assert result.exit_code != 0
    assert "nope" in result.output
