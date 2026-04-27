"""Track and retrieve the history of profile variable changes over time."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HistoryError(Exception):
    """Raised when a history operation fails."""


@dataclass
class HistoryEntry:
    profile_name: str
    context: str
    variables: dict[str, str]
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_name": self.profile_name,
            "context": self.context,
            "variables": dict(self.variables),
            "timestamp": self.timestamp,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistoryEntry":
        return cls(
            profile_name=data["profile_name"],
            context=data["context"],
            variables=data["variables"],
            timestamp=data["timestamp"],
            note=data.get("note", ""),
        )


class HistoryStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: list[HistoryEntry] = []
        if path.exists():
            raw = json.loads(path.read_text())
            self._entries = [HistoryEntry.from_dict(e) for e in raw]

    def _save(self) -> None:
        self._path.write_text(json.dumps([e.to_dict() for e in self._entries], indent=2))

    def record(self, entry: HistoryEntry) -> None:
        self._entries.append(entry)
        self._save()

    def entries_for_profile(self, profile_name: str) -> list[HistoryEntry]:
        return [e for e in self._entries if e.profile_name == profile_name]

    def all_entries(self) -> list[HistoryEntry]:
        return list(self._entries)

    def clear_profile(self, profile_name: str) -> int:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.profile_name != profile_name]
        removed = before - len(self._entries)
        if removed:
            self._save()
        return removed
