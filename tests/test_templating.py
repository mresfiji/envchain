"""Tests for envchain.templating module."""

import pytest
from envchain.templating import TemplateError, render_value, render_variables


# ---------------------------------------------------------------------------
# render_value
# ---------------------------------------------------------------------------

def test_render_value_no_placeholders():
    assert render_value("hello", {}) == "hello"


def test_render_value_simple_substitution():
    assert render_value("${HOST}", {"HOST": "localhost"}) == "localhost"


def test_render_value_inline_substitution():
    result = render_value("http://${HOST}:${PORT}", {"HOST": "example.com", "PORT": "8080"})
    assert result == "http://example.com:8080"


def test_render_value_uses_default_when_missing():
    assert render_value("${TIMEOUT:30}", {}) == "30"


def test_render_value_prefers_context_over_default():
    assert render_value("${TIMEOUT:30}", {"TIMEOUT": "60"}) == "60"


def test_render_value_empty_default_allowed():
    assert render_value("${OPTIONAL:}", {}) == ""


def test_render_value_missing_no_default_raises():
    with pytest.raises(TemplateError, match="HOST"):
        render_value("${HOST}", {})


# ---------------------------------------------------------------------------
# render_variables
# ---------------------------------------------------------------------------

def test_render_variables_plain_values():
    result = render_variables({"A": "1", "B": "2"})
    assert result == {"A": "1", "B": "2"}


def test_render_variables_self_referential():
    """A later variable may reference an earlier one in the same dict."""
    result = render_variables({"BASE_URL": "http://api.example.com", "FULL_URL": "${BASE_URL}/v1"})
    assert result["FULL_URL"] == "http://api.example.com/v1"


def test_render_variables_uses_external_context():
    result = render_variables(
        {"DSN": "postgres://${DB_USER}:${DB_PASS}@${DB_HOST}/mydb"},
        context={"DB_USER": "admin", "DB_PASS": "secret", "DB_HOST": "localhost"},
    )
    assert result["DSN"] == "postgres://admin:secret@localhost/mydb"


def test_render_variables_context_does_not_appear_in_result():
    result = render_variables({"X": "${Y}"}, context={"Y": "42"})
    assert "Y" not in result
    assert result["X"] == "42"


def test_render_variables_missing_raises_template_error():
    with pytest.raises(TemplateError):
        render_variables({"A": "${UNDEFINED_VAR}"})


def test_render_variables_default_in_batch():
    result = render_variables({"RETRIES": "${MAX_RETRIES:5}"})
    assert result["RETRIES"] == "5"
