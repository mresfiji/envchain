"""Tests for the promote CLI commands."""

import json
import pytest
from click.testing import CliRunner

from envchain.cli_promote import cli
from envchain.profile import Profile, ProfileStore


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_paths(tmp_path):
    store_path = tmp_path / "profiles.json"
    store = ProfileStore(store_path)
    store.add(Profile(name="api", context="staging", variables={"URL": "https://stg.api.io", "KEY": "abc"}))
    return {"store": str(store_path)}


def test_promote_run_creates_profile(runner, env_paths):
    result = runner.invoke(cli, ["run", "api", "production", "--store", env_paths["store"]])
    assert result.exit_code == 0
    assert "production" in result.output


def test_promote_run_with_rename(runner, env_paths):
    result = runner.invoke(
        cli,
        ["run", "api", "production", "--target-name", "api-prod", "--store", env_paths["store"]],
    )
    assert result.exit_code == 0
    store = ProfileStore(env_paths["store"])
    assert store.get("api-prod") is not None


def test_promote_run_missing_profile_fails(runner, env_paths):
    result = runner.invoke(cli, ["run", "ghost", "production", "--store", env_paths["store"]])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_promote_run_existing_target_without_overwrite_fails(runner, env_paths):
    store = ProfileStore(env_paths["store"])
    store.add(Profile(name="api", context="production", variables={"URL": "https://prod.api.io"}))
    result = runner.invoke(cli, ["run", "api", "production", "--store", env_paths["store"]])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_promote_run_overwrite_flag_succeeds(runner, env_paths):
    store = ProfileStore(env_paths["store"])
    store.add(Profile(name="api", context="production", variables={"URL": "old"}))
    result = runner.invoke(
        cli,
        ["run", "api", "production", "--overwrite", "--store", env_paths["store"]],
    )
    assert result.exit_code == 0
    assert "overwrote" in result.output
