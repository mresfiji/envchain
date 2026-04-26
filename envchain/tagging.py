"""Tag management for envchain profiles."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


class TagError(Exception):
    """Raised when a tag operation fails."""


@dataclass
class TagIndex:
    """Maps tags to sets of profile names."""

    _index: Dict[str, Set[str]] = field(default_factory=dict)

    def add(self, tag: str, profile_name: str) -> None:
        """Associate a tag with a profile."""
        tag = _normalize(tag)
        _validate_tag(tag)
        self._index.setdefault(tag, set()).add(profile_name)

    def remove(self, tag: str, profile_name: str) -> None:
        """Remove a tag association from a profile."""
        tag = _normalize(tag)
        if tag not in self._index or profile_name not in self._index[tag]:
            raise TagError(f"Profile '{profile_name}' does not have tag '{tag}'")
        self._index[tag].discard(profile_name)
        if not self._index[tag]:
            del self._index[tag]

    def profiles_for_tag(self, tag: str) -> List[str]:
        """Return sorted list of profiles associated with a tag."""
        tag = _normalize(tag)
        return sorted(self._index.get(tag, set()))

    def tags_for_profile(self, profile_name: str) -> List[str]:
        """Return sorted list of tags associated with a profile."""
        return sorted(t for t, profiles in self._index.items() if profile_name in profiles)

    def all_tags(self) -> List[str]:
        """Return all known tags."""
        return sorted(self._index.keys())

    def to_dict(self) -> Dict[str, List[str]]:
        return {tag: sorted(profiles) for tag, profiles in self._index.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, List[str]]) -> "TagIndex":
        index = cls()
        for tag, profiles in data.items():
            for profile in profiles:
                index.add(tag, profile)
        return index


def _normalize(tag: str) -> str:
    return tag.strip().lower()


def _validate_tag(tag: str) -> None:
    if not tag:
        raise TagError("Tag must not be empty")
    if not all(c.isalnum() or c in "-_" for c in tag):
        raise TagError(f"Invalid tag '{tag}': only alphanumeric, hyphens, and underscores allowed")
