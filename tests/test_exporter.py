"""Tests for the variable exporter."""

import json
import pytest
from envchain.exporter import export_variables, ExportFormatError, SUPPORTED_FORMATS


SAMPLE_VARS = {
    "APP": "myapp",
    "DEBUG": "false",
    "DB_HOST": "localhost",
}


def test_export_shell_format():
    result = export_variables(SAMPLE_VARS, fmt="shell")
    assert 'export APP="myapp"' in result
    assert 'export DEBUG="false"' in result
    assert 'export DB_HOST="localhost"' in result


def test_export_shell_quotes_special_chars():
    result = export_variables({"SECRET": "p@ss w0rd!"}, fmt="shell")
    assert "export SECRET=" in result
    assert "p@ss w0rd!" in result


def test_export_dotenv_format():
    result = export_variables(SAMPLE_VARS, fmt="dotenv")
    assert "APP=myapp" in result
    assert "DEBUG=false" in result
    assert "DB_HOST=localhost" in result
    assert "export" not in result


def test_export_json_format():
    result = export_variables(SAMPLE_VARS, fmt="json")
    parsed = json.loads(result)
    assert parsed["APP"] == "myapp"
    assert parsed["DEBUG"] == "false"
    assert parsed["DB_HOST"] == "localhost"


def test_export_json_is_sorted():
    result = export_variables(SAMPLE_VARS, fmt="json")
    parsed = json.loads(result)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_export_unsupported_format_raises():
    with pytest.raises(ExportFormatError, match="yaml"):
        export_variables(SAMPLE_VARS, fmt="yaml")


def test_export_empty_variables():
    assert export_variables({}, fmt="shell") == ""
    assert export_variables({}, fmt="dotenv") == ""
    assert json.loads(export_variables({}, fmt="json")) == {}


def test_supported_formats_constant():
    assert "shell" in SUPPORTED_FORMATS
    assert "dotenv" in SUPPORTED_FORMATS
    assert "json" in SUPPORTED_FORMATS
