"""Variable interpolation and templating for envchain profiles."""

import re
from typing import Dict, Optional


class TemplateError(Exception):
    """Raised when template rendering fails."""


_VAR_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)(?::([^}]*))?\}")


def render_value(value: str, context: Dict[str, str]) -> str:
    """Render a single value by interpolating ${VAR} or ${VAR:default} references.

    Args:
        value: The template string to render.
        context: A dict of variable names to their resolved values.

    Returns:
        The rendered string with all references substituted.

    Raises:
        TemplateError: If a variable has no value and no default is provided.
    """
    def replace(match: re.Match) -> str:
        name = match.group(1)
        default: Optional[str] = match.group(2)
        if name in context:
            return context[name]
        if default is not None:
            return default
        raise TemplateError(
            f"Variable '{name}' is not defined and has no default value."
        )

    return _VAR_PATTERN.sub(replace, value)


def render_variables(
    variables: Dict[str, str],
    context: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Render all variables in a dict, using the dict itself plus optional context.

    Variables are resolved in insertion order; a variable may reference earlier
    ones defined in the same dict.

    Args:
        variables: Mapping of variable names to (possibly templated) values.
        context: Additional variables available for interpolation.

    Returns:
        A new dict with all values fully rendered.
    """
    resolved: Dict[str, str] = dict(context or {})
    result: Dict[str, str] = {}

    for name, raw_value in variables.items():
        rendered = render_value(raw_value, resolved)
        result[name] = rendered
        resolved[name] = rendered

    return result
