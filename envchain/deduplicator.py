"""Deduplicator: remove duplicate variable values within a profile."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envchain.profile import Profile


class DeduplicatorError(Exception):
    """Raised when deduplication cannot be performed."""


@dataclass
class DeduplicateResult:
    profile_name: str
    removed_keys: List[str] = field(default_factory=list)
    kept_keys: List[str] = field(default_factory=list)
    original_variables: Dict[str, str] = field(default_factory=dict)
    deduped_variables: Dict[str, str] = field(default_factory=dict)

    @property
    def has_duplicates(self) -> bool:
        return len(self.removed_keys) > 0

    def summary(self) -> str:
        if not self.has_duplicates:
            return f"[{self.profile_name}] No duplicate values found."
        removed = ", ".join(sorted(self.removed_keys))
        return (
            f"[{self.profile_name}] Removed {len(self.removed_keys)} duplicate(s): {removed}"
        )


def deduplicate_profile(
    profile: Profile,
    keep: str = "first",
) -> DeduplicateResult:
    """Remove keys whose values are duplicates of an already-seen value.

    Parameters
    ----------
    profile:
        The profile to deduplicate.
    keep:
        ``"first"`` keeps the first occurrence of each value;
        ``"last"`` keeps the last occurrence.

    Returns
    -------
    DeduplicateResult
        Contains the cleaned variable mapping and metadata about what was
        removed.
    """
    if keep not in ("first", "last"):
        raise DeduplicatorError(f"Invalid keep strategy: {keep!r}. Use 'first' or 'last'.")

    items = list(profile.variables.items())
    if keep == "last":
        items = list(reversed(items))

    seen_values: Dict[str, str] = {}  # value -> first key that claimed it
    removed: List[str] = []
    kept: List[str] = []

    for key, value in items:
        if value in seen_values:
            removed.append(key)
        else:
            seen_values[value] = key
            kept.append(key)

    # Rebuild in original order
    original_keys_ordered = list(profile.variables.keys())
    kept_set = set(kept)
    deduped = {k: profile.variables[k] for k in original_keys_ordered if k in kept_set}

    return DeduplicateResult(
        profile_name=profile.name,
        removed_keys=sorted(removed),
        kept_keys=sorted(kept),
        original_variables=dict(profile.variables),
        deduped_variables=deduped,
    )
