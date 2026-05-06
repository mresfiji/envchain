"""Tests for envchain.cli_freeze CLI commands."""

import json
import pytest
from pathlib import Path
from click.testing import CliRunner
from envchain.cli_freeze import cli
from envchain.profile import Profile, ProfileStore


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_paths(tmp_path: Path):
    store = ProfileStore(tmp_path / "profiles.json")
    store.add_profile(Profile(name="dev", context="local", variables={"API_KEY": "abc123"}))
    store.add_profile(Profile(name="prod", context="production", variables={"DB_URL": "postgres://"}))
    return tmp_path


def test_lock_profile(runner, env_paths):
    result = runner.invoke(cli, ["lock", "dev", "--env-dir", str(env_paths)])
    assert result.exit_code == 0
    assert "frozen" in result.output


def test_lock_with_reason(runner, env_paths):
    result = runner.invoke(cli, ["lock", "prod", "--reason", "stable v1", "--env-dir", str(env_paths)])
    assert result.exit_code == 0
    assert "stable v1" in result.output


def test_lock_missing_profile_fails(runner, env_paths):
    result = runner.invoke(cli, ["lock", "ghost", "--env-dir", str(env_paths)])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "Error" in result.output


def test_lock_duplicate_fails(runner, env_paths):
    runner.invoke(cli, ["lock", "dev", "--env-dir", str(env_paths)])
    result = runner.invoke(cli, ["lock", "dev", "--env-dir", str(env_paths)])
    assert result.exit_code != 0
    assert "already frozen" in result.output


def test_unlock_profile(runner, env_paths):
    runner.invoke(cli, ["lock", "dev", "--env-dir", str(env_paths)])
    result = runner.invoke(cli, ["unlock", "dev", "--env-dir", str(env_paths)])
    assert result.exit_code == 0
    assert "unfrozen" in result.output


def test_unlock_not_frozen_fails(runner, env_paths):
    result = runner.invoke(cli, ["unlock", "dev", "--env-dir", str(env_paths)])
    assert result.exit_code != 0
    assert "not frozen" in result.output


def test_list_empty(runner, env_paths):
    result = runner.invoke(cli, ["list", "--env-dir", str(env_paths)])
    assert result.exit_code == 0
    assert "No frozen" in result.output


def test_list_shows_frozen_profiles(runner, env_paths):
    runner.invoke(cli, ["lock", "dev", "--env-dir", str(env_paths)])
    runner.invoke(cli, ["lock", "prod", "--reason", "locked", "--env-dir", str(env_paths)])
    result = runner.invoke(cli, ["list", "--env-dir", str(env_paths)])
    assert result.exit_code == 0
    assert "dev" in result.output
    assert "prod" in result.output
    assert "locked" in result.output
