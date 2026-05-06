"""Detect and report duplicate variable keys across profiles."""

from dataclasses import dataclass, field
from typing import Dict, List, Set

from envchain.profile import Profile, ProfileStore


class DuplicateError(Exception):
    """Raised when a duplicate detection operation fails."""


@dataclass
class DuplicateReport:
    """Result of scanning profiles for duplicate variable keys."""

    # Maps variable name -> list of profile names that define it
    duplicates: Dict[str, List[str]] = field(default_factory=dict)
    # All profile names that were scanned
    scanned_profiles: List[str] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.duplicates)

    def summary(self) -> str:
        if not self.has_duplicates:
            return "No duplicate variables found across {} profile(s).".format(
                len(self.scanned_profiles)
            )
        lines = [
            "Found {} duplicate variable(s) across {} profile(s):".format(
                len(self.duplicates), len(self.scanned_profiles)
            )
        ]
        for var, profiles in sorted(self.duplicates.items()):
            lines.append("  {} -> {}".format(var, ", ".join(profiles)))
        return "\n".join(lines)


def find_duplicates(profiles: List[Profile]) -> DuplicateReport:
    """Scan a list of profiles and return a report of shared variable keys."""
    seen: Dict[str, List[str]] = {}

    for profile in profiles:
        for key in profile.variables:
            seen.setdefault(key, []).append(profile.name)

    duplicates = {k: v for k, v in seen.items() if len(v) > 1}
    scanned = [p.name for p in profiles]
    return DuplicateReport(duplicates=duplicates, scanned_profiles=scanned)


def find_duplicates_in_store(
    store: ProfileStore, profile_names: List[str]
) -> DuplicateReport:
    """Load named profiles from a store and scan for duplicate variable keys."""
    profiles: List[Profile] = []
    for name in profile_names:
        profile = store.get(name)
        if profile is None:
            raise DuplicateError("Profile not found: {}".format(name))
        profiles.append(profile)
    return find_duplicates(profiles)
