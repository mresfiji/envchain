"""Profile cloning — duplicate an existing profile under a new name."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envchain.profile import Profile, ProfileStore
from envchain.validator import validate_profile_name


class CloneError(Exception):
    """Raised when a profile cannot be cloned."""


@dataclass
class CloneResult:
    source_name: str
    target_name: str
    variables_copied: int

    @property
    def summary(self) -> str:
        return (
            f"Cloned '{self.source_name}' -> '{self.target_name}' "
            f"({self.variables_copied} variable(s) copied)"
        )


def clone_profile(
    store: ProfileStore,
    source_name: str,
    target_name: str,
    context: Optional[str] = None,
    overwrite: bool = False,
) -> CloneResult:
    """Clone *source_name* into *target_name* within *store*.

    Args:
        store:       The ProfileStore to read from / write to.
        source_name: Name of the existing profile to copy.
        target_name: Name for the new profile.
        context:     Optional context override for the cloned profile.
                     Defaults to the source profile's context.
        overwrite:   If True, replace an existing profile with *target_name*.

    Returns:
        A CloneResult describing what was done.

    Raises:
        CloneError: If the source does not exist, the target already exists
                    (and *overwrite* is False), or *target_name* is invalid.
    """
    validate_profile_name(target_name)

    source = store.get(source_name)
    if source is None:
        raise CloneError(f"Source profile '{source_name}' does not exist.")

    if not overwrite and store.get(target_name) is not None:
        raise CloneError(
            f"Target profile '{target_name}' already exists. "
            "Use overwrite=True to replace it."
        )

    cloned = Profile(
        name=target_name,
        context=context if context is not None else source.context,
        variables=dict(source.variables),
    )

    store.add(cloned)
    return CloneResult(
        source_name=source_name,
        target_name=target_name,
        variables_copied=len(cloned.variables),
    )
