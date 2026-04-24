"""Tests for envchain.validator module."""

import pytest
from envchain.validator import (
    ValidationError,
    validate_variable_name,
    validate_variable_value,
    validate_variables,
    validate_profile_name,
    validate_context,
    validate_profile_dict,
)


# --- validate_variable_name ---

def test_valid_variable_names():
    for name in ["FOO", "FOO_BAR", "_PRIVATE", "VAR123"]:
        validate_variable_name(name)  # should not raise


def test_invalid_variable_name_lowercase():
    with pytest.raises(ValidationError, match="Invalid variable name"):
        validate_variable_name("foo_bar")


def test_invalid_variable_name_starts_with_digit():
    with pytest.raises(ValidationError, match="Invalid variable name"):
        validate_variable_name("1FOO")


def test_invalid_variable_name_empty():
    with pytest.raises(ValidationError, match="non-empty string"):
        validate_variable_name("")


# --- validate_variable_value ---

def test_valid_variable_value():
    validate_variable_value("some_value")  # should not raise


def test_invalid_variable_value_integer():
    with pytest.raises(ValidationError, match="must be a string"):
        validate_variable_value(42)


def test_invalid_variable_value_none():
    with pytest.raises(ValidationError, match="must be a string"):
        validate_variable_value(None)


# --- validate_variables ---

def test_valid_variables_dict():
    validate_variables({"DB_HOST": "localhost", "PORT": "5432"})


def test_invalid_variables_not_dict():
    with pytest.raises(ValidationError, match="must be a dictionary"):
        validate_variables(["FOO=bar"])


# --- validate_profile_name ---

def test_valid_profile_names():
    for name in ["base", "my-profile", "profile_1", "Prod"]:
        validate_profile_name(name)


def test_invalid_profile_name_spaces():
    with pytest.raises(ValidationError, match="Invalid profile name"):
        validate_profile_name("my profile")


# --- validate_context ---

def test_valid_contexts():
    for ctx in ["local", "staging", "production"]:
        validate_context(ctx)  # should not raise


def test_invalid_context():
    with pytest.raises(ValidationError, match="Invalid context"):
        validate_context("development")


# --- validate_profile_dict ---

def test_valid_profile_dict():
    validate_profile_dict({
        "name": "base",
        "context": "local",
        "variables": {"APP_ENV": "development"},
    })


def test_profile_dict_invalid_variable_name():
    with pytest.raises(ValidationError, match="Invalid variable name"):
        validate_profile_dict({
            "name": "base",
            "context": "local",
            "variables": {"app_env": "development"},
        })
