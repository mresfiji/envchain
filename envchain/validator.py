"""Validation utilities for envchain profiles and variable names."""

import re
from typing import Any, Dict

VAR_NAME_PATTERN = re.compile(r'^[A-Z_][A-Z0-9_]*$')
PROFILE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]+$')
VALID_CONTEXTS = {"local", "staging", "production"}


class ValidationError(Exception):
    """Raised when profile or variable validation fails."""
    pass


def validate_variable_name(name: str) -> None:
    """Ensure a variable name follows UPPER_SNAKE_CASE convention."""
    if not isinstance(name, str) or not name:
        raise ValidationError(f"Variable name must be a non-empty string, got: {name!r}")
    if not VAR_NAME_PATTERN.match(name):
        raise ValidationError(
            f"Invalid variable name {name!r}. "
            "Must match pattern: [A-Z_][A-Z0-9_]*"
        )


def validate_variable_value(value: Any) -> None:
    """Ensure a variable value is a string."""
    if not isinstance(value, str):
        raise ValidationError(
            f"Variable value must be a string, got {type(value).__name__}: {value!r}"
        )


def validate_variables(variables: Dict[str, Any]) -> None:
    """Validate all variable names and values in a dictionary."""
    if not isinstance(variables, dict):
        raise ValidationError("Variables must be a dictionary.")
    for name, value in variables.items():
        validate_variable_name(name)
        validate_variable_value(value)


def validate_profile_name(name: str) -> None:
    """Ensure a profile name contains only safe characters."""
    if not isinstance(name, str) or not name:
        raise ValidationError(f"Profile name must be a non-empty string, got: {name!r}")
    if not PROFILE_NAME_PATTERN.match(name):
        raise ValidationError(
            f"Invalid profile name {name!r}. "
            "Must match pattern: [a-zA-Z0-9_-]+"
        )


def validate_context(context: str) -> None:
    """Ensure context is one of the accepted values."""
    if context not in VALID_CONTEXTS:
        raise ValidationError(
            f"Invalid context {context!r}. Must be one of: {sorted(VALID_CONTEXTS)}"
        )


def validate_profile_dict(data: Dict[str, Any]) -> None:
    """Run full validation on a raw profile dictionary."""
    validate_profile_name(data.get("name", ""))
    validate_context(data.get("context", ""))
    validate_variables(data.get("variables", {}))
