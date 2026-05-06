"""Profile promotion: copy a profile from one context to another (e.g. staging → production)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envchain.profile import Profile, ProfileStore


class PromotionError(Exception):
    """Raised when a profile promotion fails."""


@dataclass
class PromotionResult:
    source_name: str
    source_context: str
    target_name: str
    target_context: str
    variables_promoted: int
    overwritten: bool

    def summary(self) -> str:
        action = "overwrote" if self.overwritten else "created"
        return (
            f"Promoted '{self.source_name}' ({self.source_context}) → "
            f"'{self.target_name}' ({self.target_context}): "
            f"{action} {self.variables_promoted} variable(s)."
        )


def promote_profile(
    store: ProfileStore,
    source_name: str,
    target_context: str,
    target_name: Optional[str] = None,
    overwrite: bool = False,
) -> PromotionResult:
    """Copy *source_name* into *target_context*, optionally renaming it."""
    source = store.get(source_name)
    if source is None:
        raise PromotionError(f"Source profile '{source_name}' not found.")

    resolved_target_name = target_name or source_name
    existing = store.get(resolved_target_name)
    overwritten = False

    if existing is not None:
        if not overwrite:
            raise PromotionError(
                f"Target profile '{resolved_target_name}' already exists. "
                "Pass overwrite=True to replace it."
            )
        overwritten = True

    promoted = Profile(
        name=resolved_target_name,
        context=target_context,
        variables=dict(source.variables),
    )
    store.add(promoted)

    return PromotionResult(
        source_name=source_name,
        source_context=source.context,
        target_name=resolved_target_name,
        target_context=target_context,
        variables_promoted=len(promoted.variables),
        overwritten=overwritten,
    )
