"""Schedule periodic export of environment profiles to shell files or dotenv."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class SchedulerError(Exception):
    """Raised when a schedule operation fails."""


@dataclass
class ScheduledExport:
    profile_names: List[str]
    output_path: str
    format: str  # 'shell', 'dotenv', or 'json'
    label: str
    active: bool = True

    def to_dict(self) -> dict:
        return {
            "profile_names": self.profile_names,
            "output_path": self.output_path,
            "format": self.format,
            "label": self.label,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduledExport":
        return cls(
            profile_names=data["profile_names"],
            output_path=data["output_path"],
            format=data["format"],
            label=data["label"],
            active=data.get("active", True),
        )


class ScheduleStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._schedules: List[ScheduledExport] = []
        if path.exists():
            self._load()

    def _load(self) -> None:
        data = json.loads(self.path.read_text())
        self._schedules = [ScheduledExport.from_dict(e) for e in data.get("schedules", [])]

    def _save(self) -> None:
        self.path.write_text(json.dumps({"schedules": [s.to_dict() for s in self._schedules]}, indent=2))

    def add(self, schedule: ScheduledExport) -> None:
        if any(s.label == schedule.label for s in self._schedules):
            raise SchedulerError(f"Schedule with label '{schedule.label}' already exists.")
        if schedule.format not in ("shell", "dotenv", "json"):
            raise SchedulerError(f"Unsupported format: '{schedule.format}'.")
        self._schedules.append(schedule)
        self._save()

    def remove(self, label: str) -> None:
        original = len(self._schedules)
        self._schedules = [s for s in self._schedules if s.label != label]
        if len(self._schedules) == original:
            raise SchedulerError(f"No schedule found with label '{label}'.")
        self._save()

    def get(self, label: str) -> Optional[ScheduledExport]:
        return next((s for s in self._schedules if s.label == label), None)

    def all(self) -> List[ScheduledExport]:
        return list(self._schedules)

    def active(self) -> List[ScheduledExport]:
        return [s for s in self._schedules if s.active]
