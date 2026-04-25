"""Integration tests for cli_snapshot commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envchain.cli_snapshot import cli
from envchain.profile import Profile, ProfileStore


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_paths(tmp_path: Path):
    store_path = tmp_path / "profiles.json"
    snap_path = tmp_path / "snapshots.json"
    pstore = ProfileStore(store_path)
    pstore.add_profile(
        Profile(name="local", context="local", variables={"DB_HOST": "localhost"})
    )
    pstore.add_profile(
        Profile(name="staging", context="staging", variables={"DB_HOST": "staging-db"})
    )
    return store_path, snap_path


def test_create_snapshot(runner, env_paths):
    store_path, snap_path = env_paths
    result = runner.invoke(
        cli,
        ["create", "snap1", "--profile", "local",
         "--store", str(store_path), "--snapshots", str(snap_path)],
    )
    assert result.exit_code == 0, result.output
    assert "snap1" in result.output


def test_create_snapshot_multiple_profiles(runner, env_paths):
    store_path, snap_path = env_paths
    result = runner.invoke(
        cli,
        ["create", "multi", "--profile", "local", "--profile", "staging",
         "--store", str(store_path), "--snapshots", str(snap_path)],
    )
    assert result.exit_code == 0
    data = json.loads(snap_path.read_text())
    assert "local" in data["multi"]["profiles"]
    assert "staging" in data["multi"]["profiles"]


def test_create_snapshot_missing_profile_fails(runner, env_paths):
    store_path, snap_path = env_paths
    result = runner.invoke(
        cli,
        ["create", "bad", "--profile", "ghost",
         "--store", str(store_path), "--snapshots", str(snap_path)],
    )
    assert result.exit_code != 0


def test_list_snapshots_empty(runner, env_paths):
    _, snap_path = env_paths
    result = runner.invoke(cli, ["list", "--snapshots", str(snap_path)])
    assert result.exit_code == 0
    assert "No snapshots" in result.output


def test_list_snapshots_shows_entries(runner, env_paths):
    store_path, snap_path = env_paths
    runner.invoke(
        cli,
        ["create", "mysnap", "--profile", "local", "--description", "hello",
         "--store", str(store_path), "--snapshots", str(snap_path)],
    )
    result = runner.invoke(cli, ["list", "--snapshots", str(snap_path)])
    assert "mysnap" in result.output
    assert "hello" in result.output


def test_delete_snapshot(runner, env_paths):
    store_path, snap_path = env_paths
    runner.invoke(
        cli,
        ["create", "todel", "--profile", "local",
         "--store", str(store_path), "--snapshots", str(snap_path)],
    )
    result = runner.invoke(cli, ["delete", "todel", "--snapshots", str(snap_path)])
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_delete_missing_snapshot_fails(runner, env_paths):
    _, snap_path = env_paths
    result = runner.invoke(cli, ["delete", "ghost", "--snapshots", str(snap_path)])
    assert result.exit_code != 0
