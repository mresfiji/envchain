"""Import environment variables from .env files or shell environment into profiles."""

import os
import re
from typing import Optional

from envchain.validator import validate_variables, ValidationError


class ImportError(Exception):
    """Raised when an import operation fails."""
    pass


def parse_dotenv(content: str) -> dict[str, str]:
    """Parse a .env file content into a dictionary of variables.

    Supports:
    - KEY=VALUE
    - KEY="VALUE" or KEY='VALUE'
    - Comments starting with #
    - Empty lines
    """
    variables: dict[str, str] = {}
    for line_num, line in enumerate(content.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ImportError(
                f"Line {line_num}: invalid format — expected KEY=VALUE, got: {line!r}"
            )
        key, _, raw_value = line.partition("=")
        key = key.strip()
        raw_value = raw_value.strip()

        # Strip surrounding quotes
        if (raw_value.startswith('"') and raw_value.endswith('"')) or \
           (raw_value.startswith("'") and raw_value.endswith("'")):
            raw_value = raw_value[1:-1]

        variables[key] = raw_value

    return variables


def import_from_dotenv_file(filepath: str) -> dict[str, str]:
    """Read and parse a .env file from disk."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        raise ImportError(f"Could not read file {filepath!r}: {e}") from e

    return parse_dotenv(content)


def import_from_environment(prefix: Optional[str] = None) -> dict[str, str]:
    """Import variables from the current shell environment.

    Args:
        prefix: If provided, only import variables starting with this prefix.
                The prefix is stripped from the variable names.
    """
    env = os.environ
    if prefix:
        variables = {
            key[len(prefix):]: value
            for key, value in env.items()
            if key.startswith(prefix)
        }
    else:
        variables = dict(env)
    return variables


def import_variables(
    variables: dict[str, str],
    strict: bool = True,
) -> dict[str, str]:
    """Validate and return a cleaned variable dictionary.

    Args:
        variables: Raw key-value pairs to import.
        strict: If True, raises ValidationError on invalid entries.
                If False, silently skips invalid entries.
    """
    if strict:
        validate_variables(variables)
        return dict(variables)

    clean: dict[str, str] = {}
    for key, value in variables.items():
        try:
            validate_variables({key: value})
            clean[key] = value
        except ValidationError:
            continue
    return clean
