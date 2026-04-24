"""Audit log for tracking profile access and modifications in envchain."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEntry:
    action: str
    profile_name: str
    context: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "profile_name": self.profile_name,
            "context": self.context,
            "timestamp": self.timestamp,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            action=data["action"],
            profile_name=data["profile_name"],
            context=data["context"],
            timestamp=data["timestamp"],
            details=data.get("details"),
        )


class AuditLog:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self._entries: List[AuditEntry] = []
        self._load()

    def _load(self) -> None:
        if self.log_path.exists():
            with open(self.log_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._entries = [AuditEntry.from_dict(e) for e in raw]
        else:
            self._entries = []

    def _save(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in self._entries], f, indent=2)

    def record(self, action: str, profile_name: str, context: str, details: Optional[str] = None) -> AuditEntry:
        entry = AuditEntry(
            action=action,
            profile_name=profile_name,
            context=context,
            details=details,
        )
        self._entries.append(entry)
        self._save()
        return entry

    def entries(self) -> List[AuditEntry]:
        return list(self._entries)

    def entries_for_profile(self, profile_name: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.profile_name == profile_name]

    def clear(self) -> None:
        self._entries = []
        self._save()
