"""Tests for envchain.cli_score."""
import json
import os
import pytest
from click.testing import CliRunner

from envchain.cli_score import cli
from envchain.profile import Profile, ProfileStore


@pytest.fixture()
def env_paths(tmp_path):
    store_path = str(tmp_path / "profiles.json")
    return {"ENVCHAIN_STORE": store_path}


@pytest.fixture()
def runner():
    return CliRunner()


def _seed_store(env_paths):
    store = ProfileStore(env_paths["ENVCHAIN_STORE"])
    store.add(Profile(name="web", context="production",
                      variables={"DB_URL": "pg://", "API_KEY": "k", "PORT": "80"}))
    store.add(Profile(name="empty", context="local", variables={}))
    return store


def test_score_profile_text(runner, env_paths):
    _seed_store(env_paths)
    result = runner.invoke(cli, ["run", "web"], env=env_paths)
    assert result.exit_code == 0
    assert "web" in result.output
    assert "Grade A" in result.output


def test_score_profile_json(runner, env_paths):
    _seed_store(env_paths)
    result = runner.invoke(cli, ["run", "web", "--format", "json"], env=env_paths)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["profile"] == "web"
    assert data["grade"] == "A"
    assert len(data["breakdown"]) == 4


def test_score_missing_profile_fails(runner, env_paths):
    _seed_store(env_paths)
    result = runner.invoke(cli, ["run", "nonexistent"], env=env_paths)
    assert result.exit_code != 0
    assert "not found" in result.output


def test_score_all_lists_profiles(runner, env_paths):
    _seed_store(env_paths)
    result = runner.invoke(cli, ["all"], env=env_paths)
    assert result.exit_code == 0
    assert "web" in result.output
    assert "empty" in result.output


def test_score_all_empty_store(runner, env_paths):
    # don't seed — store is empty
    result = runner.invoke(cli, ["all"], env=env_paths)
    assert result.exit_code == 0
    assert "No profiles found" in result.output


def test_score_empty_profile_grade_f(runner, env_paths):
    _seed_store(env_paths)
    result = runner.invoke(cli, ["run", "empty"], env=env_paths)
    assert result.exit_code == 0
    assert "Grade F" in result.output
