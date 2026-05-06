"""Sanitizer: redact or mask sensitive variable values in profiles."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.profile import Profile

SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"(secret|password|passwd|token|key|api_key|auth|credential)", re.IGNORECASE),
]

REDACT_PLACEHOLDER = "***REDACTED***"
MASK_CHAR = "*"


class SanitizerError(Exception):
    """Raised when sanitization fails."""


@dataclass
class SanitizeResult:
    original_name: str
    sanitized_variables: Dict[str, str]
    redacted_keys: List[str] = field(default_factory=list)
    masked_keys: List[str] = field(default_factory=list)

    def summary(self) -> str:
        parts = []
        if self.redacted_keys:
            parts.append(f"redacted: {', '.join(sorted(self.redacted_keys))}")
        if self.masked_keys:
            parts.append(f"masked: {', '.join(sorted(self.masked_keys))}")
        if not parts:
            return f"{self.original_name}: no sensitive keys detected"
        return f"{self.original_name}: " + "; ".join(parts)


def _is_sensitive(key: str) -> bool:
    return any(p.search(key) for p in SENSITIVE_PATTERNS)


def _mask_value(value: str, visible_chars: int = 4) -> str:
    if len(value) <= visible_chars:
        return MASK_CHAR * len(value)
    return value[:visible_chars] + MASK_CHAR * (len(value) - visible_chars)


def sanitize_profile(
    profile: Profile,
    mode: str = "redact",
    extra_keys: Optional[List[str]] = None,
) -> SanitizeResult:
    """Return a SanitizeResult with sensitive values redacted or masked.

    Args:
        profile: The profile to sanitize.
        mode: Either 'redact' (replace with placeholder) or 'mask' (partial hide).
        extra_keys: Additional key names to treat as sensitive.
    """
    if mode not in ("redact", "mask"):
        raise SanitizerError(f"Unknown sanitize mode: {mode!r}. Use 'redact' or 'mask'.")

    sensitive_set = set(extra_keys or [])
    sanitized: Dict[str, str] = {}
    redacted_keys: List[str] = []
    masked_keys: List[str] = []

    for key, value in profile.variables.items():
        if _is_sensitive(key) or key in sensitive_set:
            if mode == "redact":
                sanitized[key] = REDACT_PLACEHOLDER
                redacted_keys.append(key)
            else:
                sanitized[key] = _mask_value(value)
                masked_keys.append(key)
        else:
            sanitized[key] = value

    return SanitizeResult(
        original_name=profile.name,
        sanitized_variables=sanitized,
        redacted_keys=redacted_keys,
        masked_keys=masked_keys,
    )
