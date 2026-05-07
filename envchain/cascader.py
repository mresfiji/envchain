"""Cascade environment variable profiles by merging a chain of profiles in order."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.profile import Profile, ProfileStore


class CascadeError(Exception):
    """Raised when a cascade operation fails."""


@dataclass
class CascadeResult:
    profile_names: List[str]
    merged_variables: Dict[str, str]
    override_map: Dict[str, str] = field(default_factory=dict)  # key -> last profile that set it

    def summary(self) -> str:
        n = len(self.merged_variables)
        chain = " -> ".join(self.profile_names)
        return f"Cascaded {len(self.profile_names)} profiles ({chain}): {n} variable(s) resolved."


def cascade_profiles(
    profile_names: List[str],
    store: ProfileStore,
    base_variables: Optional[Dict[str, str]] = None,
) -> CascadeResult:
    """Merge profiles left-to-right; later profiles override earlier ones.

    Args:
        profile_names: Ordered list of profile names to cascade.
        store: ProfileStore to load profiles from.
        base_variables: Optional seed variables applied before any profile.

    Returns:
        CascadeResult with the merged variable set and provenance map.

    Raises:
        CascadeError: If profile_names is empty or a profile is not found.
    """
    if not profile_names:
        raise CascadeError("At least one profile name is required for a cascade.")

    merged: Dict[str, str] = dict(base_variables or {})
    override_map: Dict[str, str] = {k: "<base>" for k in merged}

    for name in profile_names:
        profile = store.get(name)
        if profile is None:
            raise CascadeError(f"Profile not found: {name!r}")
        for key, value in profile.variables.items():
            merged[key] = value
            override_map[key] = name

    return CascadeResult(
        profile_names=list(profile_names),
        merged_variables=merged,
        override_map=override_map,
    )
