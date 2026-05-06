"""Integration tests: scorer + CLI round-trip."""
import json
import pytest
from click.testing import CliRunner

from envchain.cli_score import cli
from envchain.profile import Profile, ProfileStore
from envchain.scorer import score_profile


@pytest.fixture()
def populated_store(tmp_path):
    path = str(tmp_path / "profiles.json")
    store = ProfileStore(path)
    store.add(Profile("alpha", "production", {"A": "1", "B": "2", "C": "3"}))
    store.add(Profile("beta", "staging", {"X": "", "Y": "ok"}))
    store.add(Profile("gamma", "unknown_ctx", {"K": "v", "L": "w", "M": "x"}))
    return path


@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_score_matches_library_score(populated_store, runner):
    """CLI JSON output must match direct library call."""
    store = ProfileStore(populated_store)
    profile = store.get("alpha")
    expected = score_profile(profile)

    result = runner.invoke(
        cli, ["run", "alpha", "--format", "json"],
        env={"ENVCHAIN_STORE": populated_store},
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total"] == expected.total
    assert data["grade"] == expected.grade
    assert data["percentage"] == expected.percentage


def test_cli_score_all_includes_all_profiles(populated_store, runner):
    result = runner.invoke(
        cli, ["all"],
        env={"ENVCHAIN_STORE": populated_store},
    )
    assert result.exit_code == 0
    for name in ("alpha", "beta", "gamma"):
        assert name in result.output


def test_partial_score_profile(populated_store, runner):
    """beta has an empty value — should not score 100."""
    result = runner.invoke(
        cli, ["run", "beta", "--format", "json"],
        env={"ENVCHAIN_STORE": populated_store},
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total"] < 100


def test_unknown_context_profile_score(populated_store, runner):
    """gamma has unknown context — valid_context category should score 0."""
    result = runner.invoke(
        cli, ["run", "gamma", "--format", "json"],
        env={"ENVCHAIN_STORE": populated_store},
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    ctx_item = next(b for b in data["breakdown"] if b["category"] == "valid_context")
    assert ctx_item["points"] == 0
