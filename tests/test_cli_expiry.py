"""Tests for envchain.cli_expiry."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from envchain.cli_expiry import cli

FUTURE = "2099-01-01T00:00:00+00:00"
PAST = "2000-01-01T00:00:00+00:00"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_paths(tmp_path: Path):
    return {"ENVCHAIN_EXPIRY_STORE": str(tmp_path / "expiry.json")}


def test_set_expiry(runner, env_paths):
    result = runner.invoke(cli, ["set", "prod", "API_KEY", FUTURE], env=env_paths)
    assert result.exit_code == 0
    assert "prod::API_KEY" in result.output


def test_set_expiry_with_note(runner, env_paths):
    result = runner.invoke(
        cli, ["set", "prod", "DB_PASS", FUTURE, "--note", "rotate quarterly"], env=env_paths
    )
    assert result.exit_code == 0


def test_set_invalid_date_fails(runner, env_paths):
    result = runner.invoke(cli, ["set", "prod", "API_KEY", "not-a-date"], env=env_paths)
    assert result.exit_code != 0
    assert "Invalid date" in result.output


def test_list_entries(runner, env_paths):
    runner.invoke(cli, ["set", "prod", "API_KEY", FUTURE], env=env_paths)
    result = runner.invoke(cli, ["list"], env=env_paths)
    assert result.exit_code == 0
    assert "prod::API_KEY" in result.output


def test_list_expired_only(runner, env_paths):
    runner.invoke(cli, ["set", "prod", "OLD_KEY", PAST], env=env_paths)
    runner.invoke(cli, ["set", "prod", "NEW_KEY", FUTURE], env=env_paths)
    result = runner.invoke(cli, ["list", "--expired-only"], env=env_paths)
    assert result.exit_code == 0
    assert "OLD_KEY" in result.output
    assert "NEW_KEY" not in result.output


def test_unset_entry(runner, env_paths):
    runner.invoke(cli, ["set", "prod", "API_KEY", FUTURE], env=env_paths)
    result = runner.invoke(cli, ["unset", "prod", "API_KEY"], env=env_paths)
    assert result.exit_code == 0
    assert "removed" in result.output


def test_unset_missing_fails(runner, env_paths):
    result = runner.invoke(cli, ["unset", "prod", "MISSING"], env=env_paths)
    assert result.exit_code != 0


def test_check_no_expired(runner, env_paths):
    runner.invoke(cli, ["set", "prod", "API_KEY", FUTURE], env=env_paths)
    result = runner.invoke(cli, ["check"], env=env_paths)
    assert result.exit_code == 0
    assert "No expired" in result.output


def test_check_fail_on_expired_exits_1(runner, env_paths):
    runner.invoke(cli, ["set", "prod", "OLD", PAST], env=env_paths)
    result = runner.invoke(cli, ["check", "--fail-on-expired"], env=env_paths)
    assert result.exit_code == 1
