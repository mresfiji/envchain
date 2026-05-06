"""Variable interpolation: resolve references between profiles and inject into strings."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.profile import Profile

INTERPOL_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)(?::([^}]*))?\}")


class InterpolationError(Exception):
    """Raised when a variable reference cannot be resolved."""


@dataclass
class InterpolationResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    unresolved: List[str] = field(default_factory=list)
    substitutions: int = 0

    @property
    def has_unresolved(self) -> bool:
        return bool(self.unresolved)

    def summary(self) -> str:
        parts = [f"{self.substitutions} substitution(s) made"]
        if self.unresolved:
            parts.append(f"{len(self.unresolved)} unresolved: {', '.join(self.unresolved)}")
        return "; ".join(parts)


def interpolate_value(value: str, context: Dict[str, str]) -> tuple[str, int]:
    """Interpolate a single value string using context. Returns (result, count)."""
    count = 0

    def replacer(match: re.Match) -> str:
        nonlocal count
        key = match.group(1)
        default = match.group(2)
        if key in context:
            count += 1
            return context[key]
        if default is not None:
            count += 1
            return default
        return match.group(0)

    result = INTERPOL_PATTERN.sub(replacer, value)
    return result, count


def interpolate_profile(
    profile: Profile,
    context: Optional[Dict[str, str]] = None,
    strict: bool = False,
) -> InterpolationResult:
    """Interpolate all variables in a profile using its own variables plus optional context."""
    base_context: Dict[str, str] = dict(profile.variables)
    if context:
        base_context.update(context)

    result = InterpolationResult()

    for key, raw_value in profile.variables.items():
        resolved_value, count = interpolate_value(raw_value, base_context)
        result.resolved[key] = resolved_value
        result.substitutions += count

        remaining = INTERPOL_PATTERN.findall(resolved_value)
        for unresolved_key, _ in remaining:
            if unresolved_key not in result.unresolved:
                result.unresolved.append(unresolved_key)

    if strict and result.has_unresolved:
        raise InterpolationError(
            f"Unresolved variable references: {', '.join(result.unresolved)}"
        )

    return result
