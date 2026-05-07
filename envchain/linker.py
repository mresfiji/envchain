"""Profile linker: create named symbolic links between profiles so one profile
inherits variables from another at resolution time."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class LinkError(Exception):
    """Raised when a profile link operation fails."""


@dataclass
class LinkEntry:
    source: str          # profile that owns the alias
    target: str          # profile being pointed to
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return {"source": self.source, "target": self.target, "note": self.note}

    @classmethod
    def from_dict(cls, data: dict) -> "LinkEntry":
        return cls(source=data["source"], target=data["target"], note=data.get("note"))


@dataclass
class LinkStore:
    _path: Path
    _entries: Dict[str, LinkEntry] = field(default_factory=dict)  # key = source

    def __post_init__(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._entries = {
                k: LinkEntry.from_dict(v) for k, v in raw.items()
            }

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._entries.items()}, indent=2)
        )

    def link(self, source: str, target: str, note: Optional[str] = None) -> LinkEntry:
        if source == target:
            raise LinkError(f"Cannot link profile '{source}' to itself.")
        if source in self._entries:
            raise LinkError(f"Profile '{source}' already has a link. Unlink first.")
        entry = LinkEntry(source=source, target=target, note=note)
        self._entries[source] = entry
        self._save()
        return entry

    def unlink(self, source: str) -> None:
        if source not in self._entries:
            raise LinkError(f"No link found for profile '{source}'.")
        del self._entries[source]
        self._save()

    def get(self, source: str) -> Optional[LinkEntry]:
        return self._entries.get(source)

    def all_entries(self) -> List[LinkEntry]:
        return list(self._entries.values())

    def targets_for(self, source: str) -> List[str]:
        """Return the chain of targets, following links transitively (cycle-safe)."""
        visited: List[str] = []
        current = source
        seen = set()
        while current in self._entries:
            if current in seen:
                break
            seen.add(current)
            current = self._entries[current].target
            visited.append(current)
        return visited
