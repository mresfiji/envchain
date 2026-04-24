"""Exports resolved environment variable chains to various formats."""

from typing import Dict
import json
import shlex


SUPPORTED_FORMATS = ("shell", "dotenv", "json")


class ExportFormatError(Exception):
    """Raised when an unsupported export format is requested."""
    pass


def export_shell(variables: Dict[str, str]) -> str:
    """Export variables as shell export statements.

    Example output:
        export APP="myapp"
        export DEBUG="false"
    """
    lines = [f"export {key}={shlex.quote(value)}" for key, value in sorted(variables.items())]
    return "\n".join(lines)


def export_dotenv(variables: Dict[str, str]) -> str:
    """Export variables in .env file format.

    Example output:
        APP=myapp
        DEBUG=false
    """
    lines = [f"{key}={value}" for key, value in sorted(variables.items())]
    return "\n".join(lines)


def export_json(variables: Dict[str, str]) -> str:
    """Export variables as a JSON object."""
    return json.dumps(variables, indent=2, sort_keys=True)


def export_variables(variables: Dict[str, str], fmt: str = "shell") -> str:
    """Export resolved variables in the specified format.

    Args:
        variables: Dictionary of environment variable key-value pairs.
        fmt: Output format — one of 'shell', 'dotenv', or 'json'.

    Returns:
        Formatted string representation of the variables.

    Raises:
        ExportFormatError: If the format is not supported.
    """
    if fmt == "shell":
        return export_shell(variables)
    elif fmt == "dotenv":
        return export_dotenv(variables)
    elif fmt == "json":
        return export_json(variables)
    else:
        raise ExportFormatError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )
