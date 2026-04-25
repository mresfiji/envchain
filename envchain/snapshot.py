"""Snapshot module for capturing and restoring profile states."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


@dataclass
class Snapshot:
    """Represents a point-in-time capture of one or more profiles."""

    name: str
    profiles: Dict[str, Dict[str, str]]
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "profiles": self.profiles,
            "created_at": self.created_at,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            name=data["name"],
            profiles=data["profiles"],
            created_at=data.get("created_at", ""),
            description=data.get("description", ""),
        )


class SnapshotStore:
    """Persists and retrieves snapshots from a JSON file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._snapshots: Dict[str, Snapshot] = {}
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        self._snapshots = {
            name: Snapshot.from_dict(data) for name, data in raw.items()
        }

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(
                {name: s.to_dict() for name, s in self._snapshots.items()},
                fh,
                indent=2,
            )

    def save_snapshot(self, snapshot: Snapshot) -> None:
        if not snapshot.name:
            raise SnapshotError("Snapshot name must not be empty.")
        self._snapshots[snapshot.name] = snapshot
        self._save()

    def get_snapshot(self, name: str) -> Snapshot:
        if name not in self._snapshots:
            raise SnapshotError(f"Snapshot '{name}' not found.")
        return self._snapshots[name]

    def list_snapshots(self) -> List[Snapshot]:
        return sorted(self._snapshots.values(), key=lambda s: s.created_at)

    def delete_snapshot(self, name: str) -> None:
        if name not in self._snapshots:
            raise SnapshotError(f"Snapshot '{name}' not found.")
        del self._snapshots[name]
        self._save()
