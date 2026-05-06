"""Profile summarizer: generates human-readable summaries of profiles and stores."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envchain.profile import Profile, ProfileStore


@dataclass
class ProfileSummary:
    name: str
    context: str
    variable_count: int
    variable_names: List[str] = field(default_factory=list)
    has_empty_values: bool = False
    note: Optional[str] = None

    def short(self) -> str:
        flags = " [has empty values]" if self.has_empty_values else ""
        return f"{self.name} ({self.context}) — {self.variable_count} var(s){flags}"

    def detail(self) -> str:
        lines = [
            f"Profile : {self.name}",
            f"Context : {self.context}",
            f"Variables ({self.variable_count}): {', '.join(self.variable_names) or '(none)'}",
        ]
        if self.has_empty_values:
            lines.append("Warning : one or more values are empty")
        if self.note:
            lines.append(f"Note    : {self.note}")
        return "\n".join(lines)


@dataclass
class StoreSummary:
    total_profiles: int
    contexts: List[str]
    profiles: List[ProfileSummary] = field(default_factory=list)

    def short(self) -> str:
        ctx_str = ", ".join(sorted(set(self.contexts))) or "(none)"
        return f"{self.total_profiles} profile(s) across contexts: {ctx_str}"


def summarize_profile(profile: Profile, note: Optional[str] = None) -> ProfileSummary:
    """Return a summary for a single Profile."""
    names = sorted(profile.variables.keys())
    has_empty = any(v == "" for v in profile.variables.values())
    return ProfileSummary(
        name=profile.name,
        context=profile.context,
        variable_count=len(names),
        variable_names=names,
        has_empty_values=has_empty,
        note=note,
    )


def summarize_store(store: ProfileStore) -> StoreSummary:
    """Return an aggregate summary for all profiles in a store."""
    all_profiles = store.list_profiles()
    summaries = [summarize_profile(p) for p in all_profiles]
    contexts = [p.context for p in all_profiles]
    return StoreSummary(
        total_profiles=len(summaries),
        contexts=contexts,
        profiles=summaries,
    )
