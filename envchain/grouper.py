"""Profile grouping — organise profiles into named groups."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


class GroupError(Exception):
    """Raised when a grouping operation fails."""


@dataclass
class GroupIndex:
    """Maps group names to lists of profile names."""
    _data: Dict[str, List[str]] = field(default_factory=dict)

    def add(self, group: str, profile: str) -> None:
        if not group:
            raise GroupError("Group name must not be empty.")
        if not profile:
            raise GroupError("Profile name must not be empty.")
        self._data.setdefault(group, [])
        if profile not in self._data[group]:
            self._data[group].append(profile)

    def remove(self, group: str, profile: str) -> None:
        if group not in self._data:
            raise GroupError(f"Group '{group}' does not exist.")
        if profile not in self._data[group]:
            raise GroupError(f"Profile '{profile}' is not in group '{group}'.")
        self._data[group].remove(profile)
        if not self._data[group]:
            del self._data[group]

    def profiles_for_group(self, group: str) -> List[str]:
        return list(self._data.get(group, []))

    def groups_for_profile(self, profile: str) -> List[str]:
        return [g for g, members in self._data.items() if profile in members]

    def all_groups(self) -> List[str]:
        return list(self._data.keys())

    def to_dict(self) -> Dict[str, List[str]]:
        return {k: list(v) for k, v in self._data.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, List[str]]) -> "GroupIndex":
        obj = cls()
        obj._data = {k: list(v) for k, v in data.items()}
        return obj


def load_index(path: Path) -> GroupIndex:
    if not path.exists():
        return GroupIndex()
    return GroupIndex.from_dict(json.loads(path.read_text()))


def save_index(index: GroupIndex, path: Path) -> None:
    path.write_text(json.dumps(index.to_dict(), indent=2))
