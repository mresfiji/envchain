"""Profile comparator: compare two profiles or snapshots across contexts."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.profile import Profile


class CompareError(Exception):
    """Raised when a comparison cannot be performed."""


@dataclass
class CompareResult:
    left_name: str
    right_name: str
    only_in_left: Dict[str, str] = field(default_factory=dict)
    only_in_right: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (left_val, right_val)
    unchanged: Dict[str, str] = field(default_factory=dict)

    def has_differences(self) -> bool:
        return bool(self.only_in_left or self.only_in_right or self.changed)

    def summary(self) -> str:
        parts = []
        if self.only_in_left:
            parts.append(f"{len(self.only_in_left)} only in '{self.left_name}'")
        if self.only_in_right:
            parts.append(f"{len(self.only_in_right)} only in '{self.right_name}'")
        if self.changed:
            parts.append(f"{len(self.changed)} changed")
        if self.unchanged:
            parts.append(f"{len(self.unchanged)} unchanged")
        return ", ".join(parts) if parts else "no differences"


def compare_profiles(left: Profile, right: Profile) -> CompareResult:
    """Compare two Profile objects and return a CompareResult."""
    result = CompareResult(left_name=left.name, right_name=right.name)
    left_vars = left.variables
    right_vars = right.variables
    all_keys = set(left_vars) | set(right_vars)

    for key in sorted(all_keys):
        in_left = key in left_vars
        in_right = key in right_vars
        if in_left and not in_right:
            result.only_in_left[key] = left_vars[key]
        elif in_right and not in_left:
            result.only_in_right[key] = right_vars[key]
        elif left_vars[key] != right_vars[key]:
            result.changed[key] = (left_vars[key], right_vars[key])
        else:
            result.unchanged[key] = left_vars[key]

    return result


def format_compare(result: CompareResult, mask_values: bool = True) -> List[str]:
    """Return a human-readable list of lines describing the comparison."""
    lines = []
    mask = lambda v: "***" if mask_values else v

    for key, val in sorted(result.only_in_left.items()):
        lines.append(f"< {key}={mask(val)}")
    for key, val in sorted(result.only_in_right.items()):
        lines.append(f"> {key}={mask(val)}")
    for key, (lv, rv) in sorted(result.changed.items()):
        lines.append(f"~ {key}: {mask(lv)} -> {mask(rv)}")
    for key in sorted(result.unchanged):
        lines.append(f"  {key}=(unchanged)")

    return lines
