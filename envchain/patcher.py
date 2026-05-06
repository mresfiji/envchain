"""Patch individual variables within a profile, recording changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.profile import ProfileStore


class PatchError(Exception):
    """Raised when a patch operation fails."""


@dataclass
class PatchResult:
    profile_name: str
    applied: Dict[str, str] = field(default_factory=dict)   # key -> new value
    skipped: List[str] = field(default_factory=list)         # keys not found
    previous: Dict[str, str] = field(default_factory=dict)  # key -> old value

    @property
    def has_changes(self) -> bool:
        return bool(self.applied)

    def summary(self) -> str:
        parts = []
        if self.applied:
            parts.append(f"{len(self.applied)} key(s) patched")
        if self.skipped:
            parts.append(f"{len(self.skipped)} key(s) skipped (not found)")
        return ", ".join(parts) if parts else "no changes"


def patch_profile(
    store: ProfileStore,
    profile_name: str,
    patches: Dict[str, str],
    *,
    add_missing: bool = False,
    dry_run: bool = False,
) -> PatchResult:
    """Apply key/value patches to an existing profile.

    Args:
        store: The ProfileStore to read from and write to.
        profile_name: Name of the profile to patch.
        patches: Mapping of variable names to their new values.
        add_missing: If True, add keys that do not yet exist in the profile.
        dry_run: If True, compute the result but do not persist changes.

    Returns:
        A PatchResult describing what was applied and what was skipped.

    Raises:
        PatchError: If the profile does not exist.
    """
    profile = store.get(profile_name)
    if profile is None:
        raise PatchError(f"Profile '{profile_name}' not found.")

    result = PatchResult(profile_name=profile_name)

    for key, new_value in patches.items():
        if key in profile.variables:
            result.previous[key] = profile.variables[key]
            result.applied[key] = new_value
        elif add_missing:
            result.previous[key] = ""
            result.applied[key] = new_value
        else:
            result.skipped.append(key)

    if not dry_run and result.applied:
        updated_vars = dict(profile.variables)
        updated_vars.update(result.applied)
        profile.variables = updated_vars
        store.add(profile)

    return result
