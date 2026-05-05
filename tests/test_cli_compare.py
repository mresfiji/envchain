"""Tests for envchain.cli_compare."""

import json
import pytest
from click.testing import CliRunner
from envchain.cli_compare import cli
from envchain.profile import ProfileStore, Profile


@pytest.fixture
def env_paths(tmp_path):
    store_path = str(tmp_path / "store.json")
    ps = ProfileStore(store_path)
    ps.add(Profile(name="base", context="local", variables={"FOO": "bar", "SHARED": "same"}))
    ps.add(Profile(name="override", context="staging", variables={"SHARED": "same", "EXTRA": "val"}))
    ps.add(Profile(name="changed", context="production", variables={"FOO": "newbar", "SHARED": "different"}))
    return store_path


@pytest.fixture
def runner():
    return CliRunner()


def test_compare_identical_shared_key(runner, env_paths):
    result = runner.invoke(cli, ["profiles", "base", "override", "--store", env_paths])
    assert result.exit_code == 0
    assert "Summary:" in result.output


def test_compare_shows_differences(runner, env_paths):
    result = runner.invoke(cli, ["profiles", "base", "changed", "--store", env_paths])
    assert result.exit_code == 0
    assert "changed" in result.output


def test_compare_missing_left_profile_fails(runner, env_paths):
    result = runner.invoke(cli, ["profiles", "nonexistent", "base", "--store", env_paths])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_compare_missing_right_profile_fails(runner, env_paths):
    result = runner.invoke(cli, ["profiles", "base", "ghost", "--store", env_paths])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_compare_json_output(runner, env_paths):
    result = runner.invoke(cli, ["profiles", "base", "changed", "--store", env_paths, "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["left"] == "base"
    assert data["right"] == "changed"
    assert "has_differences" in data
    assert data["has_differences"] is True


def test_compare_json_masks_values_by_default(runner, env_paths):
    result = runner.invoke(cli, ["profiles", "base", "changed", "--store", env_paths, "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    for key, entry in data.get("changed", {}).items():
        assert entry["left"] == "***"
        assert entry["right"] == "***"


def test_compare_json_shows_values_with_flag(runner, env_paths):
    result = runner.invoke(
        cli, ["profiles", "base", "changed", "--store", env_paths, "--format", "json", "--show-values"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    for key, entry in data.get("changed", {}).items():
        assert entry["left"] != "***"
