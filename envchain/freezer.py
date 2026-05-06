"""Freezer: create read-only frozen snapshots of profiles that cannot be modified."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class FreezeError(Exception):
    """Raised when a freeze or unfreeze operation fails."""


@dataclass
class FreezeEntry:
    profile_name: str
    context: str
    variables: Dict[str, str]
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "profile_name": self.profile_name,
            "context": self.context,
            "variables": self.variables,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FreezeEntry":
        return cls(
            profile_name=data["profile_name"],
            context=data["context"],
            variables=data["variables"],
            reason=data.get("reason"),
        )


class FreezeStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: Dict[str, FreezeEntry] = {}
        if path.exists():
            raw = json.loads(path.read_text())
            self._entries = {
                k: FreezeEntry.from_dict(v) for k, v in raw.items()
            }

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._entries.items()}, indent=2)
        )

    def freeze(self, profile_name: str, context: str, variables: Dict[str, str], reason: Optional[str] = None) -> FreezeEntry:
        if profile_name in self._entries:
            raise FreezeError(f"Profile '{profile_name}' is already frozen.")
        entry = FreezeEntry(profile_name=profile_name, context=context, variables=dict(variables), reason=reason)
        self._entries[profile_name] = entry
        self._save()
        return entry

    def unfreeze(self, profile_name: str) -> None:
        if profile_name not in self._entries:
            raise FreezeError(f"Profile '{profile_name}' is not frozen.")
        del self._entries[profile_name]
        self._save()

    def is_frozen(self, profile_name: str) -> bool:
        return profile_name in self._entries

    def get(self, profile_name: str) -> FreezeEntry:
        if profile_name not in self._entries:
            raise FreezeError(f"Profile '{profile_name}' is not frozen.")
        return self._entries[profile_name]

    def list_frozen(self) -> List[FreezeEntry]:
        return list(self._entries.values())
