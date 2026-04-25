"""Profile diff utility for comparing variable sets across profiles or snapshots."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class DiffResult:
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    unchanged: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        if not parts:
            return "No changes"
        return ", ".join(parts)


def diff_variables(
    before: Dict[str, str],
    after: Dict[str, str],
) -> DiffResult:
    """Compare two variable dictionaries and return a DiffResult."""
    result = DiffResult()
    all_keys = set(before) | set(after)

    for key in all_keys:
        in_before = key in before
        in_after = key in after

        if in_before and in_after:
            if before[key] != after[key]:
                result.changed[key] = (before[key], after[key])
            else:
                result.unchanged[key] = before[key]
        elif in_after:
            result.added[key] = after[key]
        else:
            result.removed[key] = before[key]

    return result


def format_diff(result: DiffResult, mask_values: bool = True) -> List[str]:
    """Format a DiffResult into human-readable lines."""
    lines = []

    def _val(v: str) -> str:
        return "***" if mask_values else v

    for key in sorted(result.added):
        lines.append(f"  + {key}={_val(result.added[key])}")

    for key in sorted(result.removed):
        lines.append(f"  - {key}={_val(result.removed[key])}")

    for key in sorted(result.changed):
        old, new = result.changed[key]
        lines.append(f"  ~ {key}: {_val(old)} -> {_val(new)}")

    return lines
