"""Tests for the profile linter module."""

import pytest
from envchain.profile import Profile
from envchain.linter import lint_profile, LintIssue, LintResult


def _make_profile(variables: dict) -> Profile:
    return Profile(name="test", context="local", variables=variables)


def test_lint_empty_profile_returns_warning():
    profile = _make_profile({})
    result = lint_profile(profile)
    assert result.has_warnings
    assert any(i.code == "W001" for i in result.issues)


def test_lint_clean_profile_returns_no_issues():
    profile = _make_profile({"APP_NAME": "myapp", "PORT": "8080"})
    result = lint_profile(profile)
    assert not result.issues
    assert not result.has_errors
    assert not result.has_warnings


def test_lint_detects_empty_value():
    profile = _make_profile({"SOME_VAR": ""})
    result = lint_profile(profile)
    codes = [i.code for i in result.issues]
    assert "W002" in codes


def test_lint_detects_weak_secret():
    profile = _make_profile({"API_SECRET": "abc"})
    result = lint_profile(profile)
    assert result.has_errors
    assert any(i.code == "E001" for i in result.issues)


def test_lint_strong_secret_passes():
    profile = _make_profile({"API_SECRET": "s3cur3P@ssword!"})
    result = lint_profile(profile)
    assert not any(i.code == "E001" for i in result.issues)


def test_lint_detects_placeholder_value():
    profile = _make_profile({"DB_HOST": "CHANGEME"})
    result = lint_profile(profile)
    assert result.has_errors
    assert any(i.code == "E002" for i in result.issues)


def test_lint_detects_todo_placeholder():
    profile = _make_profile({"ENDPOINT": "TODO"})
    result = lint_profile(profile)
    assert any(i.code == "E002" for i in result.issues)


def test_lint_detects_leading_whitespace():
    profile = _make_profile({"HOST": " localhost"})
    result = lint_profile(profile)
    assert any(i.code == "W003" for i in result.issues)


def test_lint_detects_trailing_whitespace():
    profile = _make_profile({"HOST": "localhost "})
    result = lint_profile(profile)
    assert any(i.code == "W003" for i in result.issues)


def test_lint_result_summary():
    profile = _make_profile({"API_KEY": "x", "VAR": "CHANGEME"})
    result = lint_profile(profile)
    summary = result.summary()
    assert "test" in summary
    assert "error" in summary


def test_lint_issue_to_dict():
    issue = LintIssue(level="error", code="E001", message="Bad value", variable="MY_VAR")
    d = issue.to_dict()
    assert d["level"] == "error"
    assert d["code"] == "E001"
    assert d["variable"] == "MY_VAR"


def test_lint_multiple_issues_on_same_profile():
    profile = _make_profile({
        "DB_PASSWORD": "x",
        "HOST": " example ",
        "TOKEN": "PLACEHOLDER",
    })
    result = lint_profile(profile)
    assert len(result.issues) >= 3
