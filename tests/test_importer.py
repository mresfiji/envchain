"""Tests for envchain.importer module."""

import os
import pytest

from envchain.importer import (
    ImportError,
    parse_dotenv,
    import_from_dotenv_file,
    import_from_environment,
    import_variables,
)
from envchain.validator import ValidationError


# --- parse_dotenv ---

def test_parse_dotenv_basic():
    content = "FOO=bar\nBAZ=qux\n"
    result = parse_dotenv(content)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_dotenv_ignores_comments_and_blank_lines():
    content = "# comment\n\nFOO=hello\n"
    result = parse_dotenv(content)
    assert result == {"FOO": "hello"}


def test_parse_dotenv_strips_double_quotes():
    content = 'DB_URL="postgres://localhost/mydb"'
    result = parse_dotenv(content)
    assert result == {"DB_URL": "postgres://localhost/mydb"}


def test_parse_dotenv_strips_single_quotes():
    content = "SECRET='my secret value'"
    result = parse_dotenv(content)
    assert result == {"SECRET": "my secret value"}


def test_parse_dotenv_value_with_equals_sign():
    content = "TOKEN=abc=def=ghi"
    result = parse_dotenv(content)
    assert result == {"TOKEN": "abc=def=ghi"}


def test_parse_dotenv_invalid_line_raises():
    content = "INVALID_LINE_NO_EQUALS"
    with pytest.raises(ImportError, match="invalid format"):
        parse_dotenv(content)


# --- import_from_dotenv_file ---

def test_import_from_dotenv_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=staging\nPORT=8080\n")
    result = import_from_dotenv_file(str(env_file))
    assert result == {"APP_ENV": "staging", "PORT": "8080"}


def test_import_from_dotenv_file_missing_raises():
    with pytest.raises(ImportError, match="Could not read file"):
        import_from_dotenv_file("/nonexistent/path/.env")


# --- import_from_environment ---

def test_import_from_environment_no_prefix(monkeypatch):
    monkeypatch.setenv("MY_VAR", "hello")
    result = import_from_environment()
    assert "MY_VAR" in result
    assert result["MY_VAR"] == "hello"


def test_import_from_environment_with_prefix(monkeypatch):
    monkeypatch.setenv("APP_HOST", "localhost")
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("OTHER_VAR", "ignored")
    result = import_from_environment(prefix="APP_")
    assert "HOST" in result
    assert "PORT" in result
    assert "OTHER_VAR" not in result


# --- import_variables ---

def test_import_variables_strict_valid():
    variables = {"VALID_KEY": "some_value"}
    result = import_variables(variables, strict=True)
    assert result == variables


def test_import_variables_strict_invalid_raises():
    with pytest.raises(ValidationError):
        import_variables({"invalid-key": "value"}, strict=True)


def test_import_variables_non_strict_skips_invalid():
    variables = {"VALID_KEY": "ok", "bad-key": "skip"}
    result = import_variables(variables, strict=False)
    assert "VALID_KEY" in result
    assert "bad-key" not in result
