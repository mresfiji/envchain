"""Tests for envchain.cli_group."""
import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from envchain.cli_group import cli


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_paths(tmp_path):
    index_file = tmp_path / "groups.json"
    return {"ENVCHAIN_GROUP_INDEX": str(index_file)}


def test_add_profile_to_group(runner, env_paths):
    result = runner.invoke(cli, ["add", "backend", "api-prod"], env=env_paths)
    assert result.exit_code == 0
    assert "Added 'api-prod' to group 'backend'" in result.output


def test_add_creates_index_file(runner, env_paths):
    runner.invoke(cli, ["add", "g", "p"], env=env_paths)
    path = Path(env_paths["ENVCHAIN_GROUP_INDEX"])
    assert path.exists()
    data = json.loads(path.read_text())
    assert "g" in data
    assert "p" in data["g"]


def test_list_profiles_in_group(runner, env_paths):
    runner.invoke(cli, ["add", "infra", "db-prod"], env=env_paths)
    runner.invoke(cli, ["add", "infra", "cache-prod"], env=env_paths)
    result = runner.invoke(cli, ["list", "infra"], env=env_paths)
    assert result.exit_code == 0
    assert "db-prod" in result.output
    assert "cache-prod" in result.output


def test_list_empty_group(runner, env_paths):
    result = runner.invoke(cli, ["list", "nonexistent"], env=env_paths)
    assert result.exit_code == 0
    assert "empty or does not exist" in result.output


def test_remove_profile_from_group(runner, env_paths):
    runner.invoke(cli, ["add", "g", "p"], env=env_paths)
    result = runner.invoke(cli, ["remove", "g", "p"], env=env_paths)
    assert result.exit_code == 0
    assert "Removed 'p' from group 'g'" in result.output


def test_remove_missing_group_fails(runner, env_paths):
    result = runner.invoke(cli, ["remove", "ghost", "p"], env=env_paths)
    assert result.exit_code != 0
    assert "Error" in result.output


def test_show_groups_for_profile(runner, env_paths):
    runner.invoke(cli, ["add", "backend", "api"], env=env_paths)
    runner.invoke(cli, ["add", "infra", "api"], env=env_paths)
    result = runner.invoke(cli, ["show", "api"], env=env_paths)
    assert result.exit_code == 0
    assert "backend" in result.output
    assert "infra" in result.output


def test_show_profile_not_in_any_group(runner, env_paths):
    result = runner.invoke(cli, ["show", "orphan"], env=env_paths)
    assert result.exit_code == 0
    assert "does not belong to any group" in result.output
