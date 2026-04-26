"""Tests for envchain.cli_scheduler."""

import json
import pytest
from click.testing import CliRunner
from pathlib import Path
from envchain.cli_scheduler import cli
from envchain.profile import Profile, ProfileStore


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_paths(tmp_path):
    schedule_file = tmp_path / "schedules.json"
    profile_file = tmp_path / "profiles.json"
    ps = ProfileStore(profile_file)
    ps.add(Profile(name="base", context="local", variables={"APP": "myapp"}))
    ps.add(Profile(name="prod", context="production", variables={"ENV": "prod"}))
    return {"schedule_file": str(schedule_file), "profile_file": str(profile_file)}


def test_add_schedule(runner, env_paths):
    result = runner.invoke(cli, [
        "add", "nightly",
        "--profiles", "base", "--profiles", "prod",
        "--output", "/tmp/out.env",
        "--format", "dotenv",
        "--schedule-file", env_paths["schedule_file"],
    ])
    assert result.exit_code == 0
    assert "added" in result.output


def test_add_duplicate_label_fails(runner, env_paths):
    for _ in range(2):
        result = runner.invoke(cli, [
            "add", "nightly",
            "--profiles", "base",
            "--output", "/tmp/out.env",
            "--schedule-file", env_paths["schedule_file"],
        ])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_list_schedules(runner, env_paths):
    runner.invoke(cli, [
        "add", "nightly", "--profiles", "base",
        "--output", "/tmp/out.env",
        "--schedule-file", env_paths["schedule_file"],
    ])
    result = runner.invoke(cli, ["list", "--schedule-file", env_paths["schedule_file"]])
    assert result.exit_code == 0
    assert "nightly" in result.output


def test_list_empty(runner, env_paths):
    result = runner.invoke(cli, ["list", "--schedule-file", env_paths["schedule_file"]])
    assert "No scheduled exports" in result.output


def test_remove_schedule(runner, env_paths):
    runner.invoke(cli, [
        "add", "nightly", "--profiles", "base",
        "--output", "/tmp/out.env",
        "--schedule-file", env_paths["schedule_file"],
    ])
    result = runner.invoke(cli, ["remove", "nightly", "--schedule-file", env_paths["schedule_file"]])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_run_schedule(runner, env_paths, tmp_path):
    out_file = tmp_path / "out.env"
    runner.invoke(cli, [
        "add", "nightly",
        "--profiles", "base", "--profiles", "prod",
        "--output", str(out_file),
        "--format", "dotenv",
        "--schedule-file", env_paths["schedule_file"],
    ])
    result = runner.invoke(cli, [
        "run", "nightly",
        "--schedule-file", env_paths["schedule_file"],
        "--profile-file", env_paths["profile_file"],
    ])
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "APP" in content
    assert "ENV" in content
