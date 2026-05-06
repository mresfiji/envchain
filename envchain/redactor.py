"""Redactor: mask or strip sensitive variable values before display or export."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.profile import Profile

_SENSITIVE_PATTERNS = (
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "auth", "credential", "private_key", "access_key", "signing_key",
)

DEFAULT_MASK = "***REDACTED***"


class RedactorError(Exception):
    """Raised when redaction fails."""


def _is_sensitive(key: str) -> bool:
    """Return True if the variable name suggests a sensitive value."""
    lower = key.lower()
    return any(pat in lower for pat in _SENSITIVE_PATTERNS)


@dataclass
class RedactResult:
    original: Dict[str, str]
    redacted: Dict[str, str]
    redacted_keys: List[str] = field(default_factory=list)

    def has_redactions(self) -> bool:
        return bool(self.redacted_keys)

    def summary(self) -> str:
        if not self.redacted_keys:
            return "No sensitive variables detected."
        keys = ", ".join(sorted(self.redacted_keys))
        return f"Redacted {len(self.redacted_keys)} sensitive variable(s): {keys}"


def redact_variables(
    variables: Dict[str, str],
    mask: str = DEFAULT_MASK,
    extra_keys: Optional[List[str]] = None,
) -> RedactResult:
    """Return a copy of *variables* with sensitive values replaced by *mask*."""
    if not isinstance(variables, dict):
        raise RedactorError("variables must be a dict")

    sensitive = set(extra_keys or [])
    redacted: Dict[str, str] = {}
    redacted_keys: List[str] = []

    for key, value in variables.items():
        if _is_sensitive(key) or key in sensitive:
            redacted[key] = mask
            redacted_keys.append(key)
        else:
            redacted[key] = value

    return RedactResult(
        original=dict(variables),
        redacted=redacted,
        redacted_keys=sorted(redacted_keys),
    )


def redact_profile(
    profile: Profile,
    mask: str = DEFAULT_MASK,
    extra_keys: Optional[List[str]] = None,
) -> RedactResult:
    """Redact sensitive variables from a Profile."""
    return redact_variables(profile.variables, mask=mask, extra_keys=extra_keys)
