"""Archive and restore profiles to/from a portable JSON bundle."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

from envchain.profile import Profile, ProfileStore


class ArchiveError(Exception):
    """Raised when archiving or restoring fails."""


@dataclass
class ArchiveResult:
    archived: List[str]  # profile names written to the bundle
    skipped: List[str]   # profile names that were not found

    def summary(self) -> str:
        parts = [f"Archived {len(self.archived)} profile(s)"]
        if self.skipped:
            parts.append(f"skipped {len(self.skipped)}: {', '.join(self.skipped)}")
        return "; ".join(parts) + "."


def archive_profiles(
    store: ProfileStore,
    profile_names: List[str],
    dest: Path,
    *,
    overwrite: bool = False,
) -> ArchiveResult:
    """Write selected profiles from *store* into a JSON bundle at *dest*."""
    if dest.exists() and not overwrite:
        raise ArchiveError(f"Destination already exists: {dest}")

    archived: List[str] = []
    skipped: List[str] = []
    bundle: dict = {}

    for name in profile_names:
        profile = store.get(name)
        if profile is None:
            skipped.append(name)
        else:
            bundle[name] = profile.to_dict()
            archived.append(name)

    dest.write_text(json.dumps(bundle, indent=2, sort_keys=True))
    return ArchiveResult(archived=archived, skipped=skipped)


def restore_profiles(
    store: ProfileStore,
    src: Path,
    *,
    overwrite: bool = False,
) -> List[str]:
    """Load profiles from a JSON bundle at *src* into *store*.

    Returns the list of profile names that were restored.
    """
    if not src.exists():
        raise ArchiveError(f"Archive file not found: {src}")

    try:
        bundle = json.loads(src.read_text())
    except json.JSONDecodeError as exc:
        raise ArchiveError(f"Invalid archive format: {exc}") from exc

    if not isinstance(bundle, dict):
        raise ArchiveError("Archive must be a JSON object mapping profile names to data.")

    restored: List[str] = []
    for name, data in bundle.items():
        if store.get(name) is not None and not overwrite:
            raise ArchiveError(
                f"Profile '{name}' already exists. Use overwrite=True to replace it."
            )
        profile = Profile.from_dict(data)
        store.add(profile)
        restored.append(name)

    return restored
