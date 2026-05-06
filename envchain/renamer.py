"""Profile renaming with history tracking and reference updates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envchain.profile import ProfileStore
from envchain.history import HistoryStore


class RenameError(Exception):
    """Raised when a profile rename operation fails."""


@dataclass
class RenameResult:
    old_name: str
    new_name: str
    context: str
    variables_count: int

    def summary(self) -> str:
        return (
            f"Renamed '{self.old_name}' -> '{self.new_name}' "
            f"[{self.context}] ({self.variables_count} variables)"
        )


def rename_profile(
    store: ProfileStore,
    old_name: str,
    new_name: str,
    context: str,
    history_store: Optional[HistoryStore] = None,
) -> RenameResult:
    """Rename a profile within a context.

    Raises RenameError if the source profile does not exist or the target
    name is already taken in the same context.
    """
    source = store.get_profile(old_name, context)
    if source is None:
        raise RenameError(
            f"Profile '{old_name}' not found in context '{context}'."
        )

    existing = store.get_profile(new_name, context)
    if existing is not None:
        raise RenameError(
            f"Profile '{new_name}' already exists in context '{context}'."
        )

    from envchain.profile import Profile

    renamed = Profile(
        name=new_name,
        context=source.context,
        variables=dict(source.variables),
    )
    store.add_profile(renamed)
    store.remove_profile(old_name, context)

    if history_store is not None:
        history_store.record(
            profile=new_name,
            context=context,
            action="rename",
            details={"from": old_name, "to": new_name},
        )

    return RenameResult(
        old_name=old_name,
        new_name=new_name,
        context=context,
        variables_count=len(renamed.variables),
    )
