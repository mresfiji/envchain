"""Profile variable expiration tracking and enforcement."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class ExpirationError(Exception):
    """Raised when an expiration operation fails."""


@dataclass
class ExpiryEntry:
    profile: str
    variable: str
    expires_at: datetime
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "profile": self.profile,
            "variable": self.variable,
            "expires_at": self.expires_at.isoformat(),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExpiryEntry":
        return cls(
            profile=data["profile"],
            variable=data["variable"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            note=data.get("note", ""),
        )

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now >= expires


class ExpiryStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: Dict[str, ExpiryEntry] = {}
        if path.exists():
            self._load()

    def _key(self, profile: str, variable: str) -> str:
        return f"{profile}::{variable}"

    def _load(self) -> None:
        data = json.loads(self._path.read_text())
        self._entries = {
            k: ExpiryEntry.from_dict(v) for k, v in data.items()
        }

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._entries.items()}, indent=2)
        )

    def set(self, entry: ExpiryEntry) -> None:
        self._entries[self._key(entry.profile, entry.variable)] = entry
        self._save()

    def get(self, profile: str, variable: str) -> Optional[ExpiryEntry]:
        return self._entries.get(self._key(profile, variable))

    def remove(self, profile: str, variable: str) -> None:
        key = self._key(profile, variable)
        if key not in self._entries:
            raise ExpirationError(f"No expiry set for {profile}::{variable}")
        del self._entries[key]
        self._save()

    def expired_entries(self, now: Optional[datetime] = None) -> List[ExpiryEntry]:
        return [e for e in self._entries.values() if e.is_expired(now)]

    def all_entries(self) -> List[ExpiryEntry]:
        return list(self._entries.values())
