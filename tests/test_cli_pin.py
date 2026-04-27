"""Tests for envchain.cli_pin."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envchain.cli_pin import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_paths(tmp_path: Path):
    return {"ENVCHAIN_HOME": str(tmp_path)}


def test_set_pin(runner, env_paths):
    result = runner.invoke(cli, ["set", "prod", "snap-001"], env=env_paths)
    assert result.exit_code == 0
    assert "Pinned 'prod'" in result.output


def test_set_pin_with_note(runner, env_paths):
    result = runner.invoke(cli, ["set", "staging", "snap-002", "--note", "v2"], env=env_paths)
    assert result.exit_code == 0
    assert "snap-002" in result.output


def test_show_pin(runner, env_paths):
    runner.invoke(cli, ["set", "prod", "snap-abc", "--note", "stable"], env=env_paths)
    result = runner.invoke(cli, ["show", "prod"], env=env_paths)
    assert result.exit_code == 0
    assert "snap-abc" in result.output
    assert "stable" in result.output


def test_show_unpinned_profile(runner, env_paths):
    result = runner.invoke(cli, ["show", "ghost"], env=env_paths)
    assert result.exit_code == 0
    assert "not pinned" in result.output


def test_unset_pin(runner, env_paths):
    runner.invoke(cli, ["set", "dev", "snap-dev"], env=env_paths)
    result = runner.invoke(cli, ["unset", "dev"], env=env_paths)
    assert result.exit_code == 0
    assert "Unpinned" in result.output


def test_unset_unknown_pin_fails(runner, env_paths):
    result = runner.invoke(cli, ["unset", "nobody"], env=env_paths)
    assert result.exit_code != 0
    assert "not pinned" in result.output


def test_list_pins(runner, env_paths):
    runner.invoke(cli, ["set", "prod", "snap-1"], env=env_paths)
    runner.invoke(cli, ["set", "dev", "snap-2"], env=env_paths)
    result = runner.invoke(cli, ["list"], env=env_paths)
    assert result.exit_code == 0
    assert "prod" in result.output
    assert "dev" in result.output


def test_list_empty(runner, env_paths):
    result = runner.invoke(cli, ["list"], env=env_paths)
    assert result.exit_code == 0
    assert "No profiles" in result.output
