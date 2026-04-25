"""Tests for envchain.differ module."""

import pytest
from envchain.differ import DiffResult, diff_variables, format_diff


BEFORE = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "API_KEY": "old-key",
}

AFTER = {
    "DB_HOST": "localhost",
    "DB_PORT": "5433",
    "NEW_VAR": "hello",
}


def test_diff_detects_added():
    result = diff_variables(BEFORE, AFTER)
    assert "NEW_VAR" in result.added
    assert result.added["NEW_VAR"] == "hello"


def test_diff_detects_removed():
    result = diff_variables(BEFORE, AFTER)
    assert "API_KEY" in result.removed
    assert result.removed["API_KEY"] == "old-key"


def test_diff_detects_changed():
    result = diff_variables(BEFORE, AFTER)
    assert "DB_PORT" in result.changed
    assert result.changed["DB_PORT"] == ("5432", "5433")


def test_diff_detects_unchanged():
    result = diff_variables(BEFORE, AFTER)
    assert "DB_HOST" in result.unchanged
    assert result.unchanged["DB_HOST"] == "localhost"


def test_has_changes_true():
    result = diff_variables(BEFORE, AFTER)
    assert result.has_changes is True


def test_has_changes_false():
    result = diff_variables(BEFORE, BEFORE)
    assert result.has_changes is False


def test_summary_no_changes():
    result = diff_variables(BEFORE, BEFORE)
    assert result.summary() == "No changes"


def test_summary_with_changes():
    result = diff_variables(BEFORE, AFTER)
    summary = result.summary()
    assert "+1 added" in summary
    assert "-1 removed" in summary
    assert "~1 changed" in summary


def test_format_diff_masks_values_by_default():
    result = diff_variables(BEFORE, AFTER)
    lines = format_diff(result)
    for line in lines:
        assert "***" in line


def test_format_diff_shows_values_when_unmasked():
    result = diff_variables(BEFORE, AFTER)
    lines = format_diff(result, mask_values=False)
    joined = "\n".join(lines)
    assert "hello" in joined
    assert "old-key" in joined
    assert "5432" in joined


def test_format_diff_prefixes():
    result = diff_variables(BEFORE, AFTER)
    lines = format_diff(result, mask_values=False)
    prefixes = {line.strip()[0] for line in lines}
    assert "+" in prefixes
    assert "-" in prefixes
    assert "~" in prefixes


def test_diff_empty_before():
    result = diff_variables({}, {"FOO": "bar"})
    assert "FOO" in result.added
    assert not result.removed


def test_diff_empty_after():
    result = diff_variables({"FOO": "bar"}, {})
    assert "FOO" in result.removed
    assert not result.added
