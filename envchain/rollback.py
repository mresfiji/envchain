"""Rollback support: restore a profile to a previous history entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from envchain.history import HistoryStore, HistoryEntry
from envchain.profile import Profile, ProfileStore


class RollbackError(Exception):
    """Raised when a rollback operation fails."""


@dataclass
class RollbackResult:
    profile_name: str
    restored_from: str  # history entry id
    previous_variables: Dict[str, str]
    restored_variables: Dict[str, str]

    @property
    def changed_keys(self) -> list[str]:
        all_keys = set(self.previous_variables) | set(self.restored_variables)
        return [
            k for k in all_keys
            if self.previous_variables.get(k) != self.restored_variables.get(k)
        ]


def rollback_profile(
    profile_name: str,
    entry_id: str,
    profile_store: ProfileStore,
    history_store: HistoryStore,
) -> RollbackResult:
    """Restore a profile's variables from a specific history entry."""
    profile = profile_store.get(profile_name)
    if profile is None:
        raise RollbackError(f"Profile '{profile_name}' not found.")

    entry: Optional[HistoryEntry] = history_store.get(entry_id)
    if entry is None:
        raise RollbackError(f"History entry '{entry_id}' not found.")

    if entry.profile_name != profile_name:
        raise RollbackError(
            f"History entry '{entry_id}' belongs to profile "
            f"'{entry.profile_name}', not '{profile_name}'."
        )

    previous_variables = dict(profile.variables)
    profile.variables = dict(entry.variables)
    profile_store.add(profile, overwrite=True)

    return RollbackResult(
        profile_name=profile_name,
        restored_from=entry_id,
        previous_variables=previous_variables,
        restored_variables=dict(entry.variables),
    )


def list_rollback_points(
    profile_name: str,
    history_store: HistoryStore,
    limit: int = 10,
) -> list[HistoryEntry]:
    """Return recent history entries available for rollback for a profile."""
    entries = [
        e for e in history_store.all()
        if e.profile_name == profile_name
    ]
    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return entries[:limit]
