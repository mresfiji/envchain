"""envchain.labeler — Attach and manage free-form labels on profiles."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set


class LabelError(Exception):
    """Raised when a label operation fails."""


@dataclass
class LabelIndex:
    _data: Dict[str, Set[str]] = field(default_factory=dict)  # profile -> labels

    def add(self, profile: str, label: str) -> None:
        label = label.strip()
        if not label:
            raise LabelError("Label must not be empty.")
        self._data.setdefault(profile, set()).add(label)

    def remove(self, profile: str, label: str) -> None:
        labels = self._data.get(profile, set())
        if label not in labels:
            raise LabelError(f"Label '{label}' not found on profile '{profile}'.")
        labels.discard(label)
        if not labels:
            del self._data[profile]

    def labels_for_profile(self, profile: str) -> List[str]:
        return sorted(self._data.get(profile, set()))

    def profiles_for_label(self, label: str) -> List[str]:
        return sorted(p for p, labels in self._data.items() if label in labels)

    def all_labels(self) -> List[str]:
        result: Set[str] = set()
        for labels in self._data.values():
            result.update(labels)
        return sorted(result)

    def to_dict(self) -> dict:
        return {p: sorted(ls) for p, ls in self._data.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "LabelIndex":
        obj = cls()
        for profile, labels in data.items():
            for label in labels:
                obj.add(profile, label)
        return obj

    @classmethod
    def load(cls, path: Path) -> "LabelIndex":
        if not path.exists():
            return cls()
        with path.open() as fh:
            return cls.from_dict(json.load(fh))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as fh:
            json.dump(self.to_dict(), fh, indent=2)
