"""Stasher: temporarily stash and restore profile variables."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envchain.profile import ProfileStore


class StashError(Exception):
    """Raised when a stash operation fails."""


@dataclass
class StashEntry:
    label: str
    profile_name: str
    variables: Dict[str, str]
    stashed_at: float = field(default_factory=time.time)
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "profile_name": self.profile_name,
            "variables": self.variables,
            "stashed_at": self.stashed_at,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StashEntry":
        return cls(
            label=data["label"],
            profile_name=data["profile_name"],
            variables=data["variables"],
            stashed_at=data.get("stashed_at", 0.0),
            note=data.get("note"),
        )


class StashStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: Dict[str, StashEntry] = {}
        if path.exists():
            raw = json.loads(path.read_text())
            self._entries = {
                k: StashEntry.from_dict(v) for k, v in raw.items()
            }

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._entries.items()}, indent=2)
        )

    def stash(self, label: str, profile_store: ProfileStore, profile_name: str, note: Optional[str] = None) -> StashEntry:
        if label in self._entries:
            raise StashError(f"Stash label '{label}' already exists; pop it first.")
        profile = profile_store.get(profile_name)
        if profile is None:
            raise StashError(f"Profile '{profile_name}' not found.")
        entry = StashEntry(
            label=label,
            profile_name=profile_name,
            variables=dict(profile.variables),
            note=note,
        )
        self._entries[label] = entry
        self._save()
        return entry

    def pop(self, label: str, profile_store: ProfileStore, restore: bool = True) -> StashEntry:
        if label not in self._entries:
            raise StashError(f"No stash entry found for label '{label}'.")
        entry = self._entries.pop(label)
        if restore:
            profile = profile_store.get(entry.profile_name)
            if profile is None:
                raise StashError(f"Profile '{entry.profile_name}' no longer exists; cannot restore.")
            profile.variables = entry.variables
            profile_store.add(profile)
        self._save()
        return entry

    def list(self) -> List[StashEntry]:
        return sorted(self._entries.values(), key=lambda e: e.stashed_at)

    def get(self, label: str) -> Optional[StashEntry]:
        return self._entries.get(label)
