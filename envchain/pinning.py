"""Profile pinning: lock a profile to a specific snapshot version."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


class PinError(Exception):
    """Raised when a pinning operation fails."""


@dataclass
class PinEntry:
    profile_name: str
    snapshot_id: str
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "profile_name": self.profile_name,
            "snapshot_id": self.snapshot_id,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PinEntry":
        return cls(
            profile_name=data["profile_name"],
            snapshot_id=data["snapshot_id"],
            note=data.get("note"),
        )


class PinStore:
    """Persist pin entries to a JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._pins: Dict[str, PinEntry] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._pins = {
                k: PinEntry.from_dict(v) for k, v in raw.items()
            }

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._pins.items()}, indent=2)
        )

    def pin(self, profile_name: str, snapshot_id: str, note: Optional[str] = None) -> PinEntry:
        entry = PinEntry(profile_name=profile_name, snapshot_id=snapshot_id, note=note)
        self._pins[profile_name] = entry
        self._save()
        return entry

    def unpin(self, profile_name: str) -> None:
        if profile_name not in self._pins:
            raise PinError(f"Profile '{profile_name}' is not pinned.")
        del self._pins[profile_name]
        self._save()

    def get(self, profile_name: str) -> Optional[PinEntry]:
        return self._pins.get(profile_name)

    def all_pins(self) -> list[PinEntry]:
        return list(self._pins.values())

    def is_pinned(self, profile_name: str) -> bool:
        return profile_name in self._pins
