"""Profile migration: rename keys across one or more profiles."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.profile import Profile, ProfileStore


class MigrationError(Exception):
    """Raised when a migration cannot be completed."""


@dataclass
class MigrationResult:
    profile_name: str
    renamed: Dict[str, str] = field(default_factory=dict)   # old_key -> new_key
    skipped: List[str] = field(default_factory=list)        # keys not found

    @property
    def has_changes(self) -> bool:
        return bool(self.renamed)

    def summary(self) -> str:
        if not self.has_changes:
            return f"{self.profile_name}: no changes"
        parts = [f"{o} -> {n}" for o, n in self.renamed.items()]
        msg = f"{self.profile_name}: renamed {', '.join(parts)}"
        if self.skipped:
            msg += f" (skipped missing: {', '.join(self.skipped)})"
        return msg


def migrate_profile(
    store: ProfileStore,
    profile_name: str,
    key_map: Dict[str, str],
    *,
    overwrite: bool = False,
) -> MigrationResult:
    """Rename keys in *key_map* (old -> new) within a single profile.

    Args:
        store: The profile store to read from / write to.
        profile_name: Name of the profile to migrate.
        key_map: Mapping of old key names to new key names.
        overwrite: If True, overwrite an existing new key; otherwise raise.

    Returns:
        A :class:`MigrationResult` describing what changed.
    """
    profile = store.get(profile_name)
    if profile is None:
        raise MigrationError(f"Profile '{profile_name}' not found.")

    result = MigrationResult(profile_name=profile_name)
    variables: Dict[str, str] = dict(profile.variables)

    for old_key, new_key in key_map.items():
        if old_key not in variables:
            result.skipped.append(old_key)
            continue
        if new_key in variables and not overwrite:
            raise MigrationError(
                f"Key '{new_key}' already exists in '{profile_name}'. "
                "Use overwrite=True to replace it."
            )
        variables[new_key] = variables.pop(old_key)
        result.renamed[old_key] = new_key

    if result.has_changes:
        updated = Profile(
            name=profile.name,
            context=profile.context,
            variables=variables,
        )
        store.add(updated)

    return result


def migrate_all(
    store: ProfileStore,
    key_map: Dict[str, str],
    *,
    context: Optional[str] = None,
    overwrite: bool = False,
) -> List[MigrationResult]:
    """Apply *key_map* to every profile in the store (optionally filtered by context)."""
    results: List[MigrationResult] = []
    for name in store.list():
        profile = store.get(name)
        if context is not None and profile.context != context:
            continue
        results.append(
            migrate_profile(store, name, key_map, overwrite=overwrite)
        )
    return results
