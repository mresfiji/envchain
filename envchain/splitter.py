"""Split a profile's variables into multiple sub-profiles by prefix or key list."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.profile import Profile, ProfileStore


class SplitError(Exception):
    """Raised when a profile split operation fails."""


@dataclass
class SplitResult:
    source: str
    created: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    def summary(self) -> str:
        parts = [f"Split '{self.source}' into {len(self.created)} profile(s)."]
        if self.skipped_keys:
            parts.append(f"Skipped {len(self.skipped_keys)} unmatched key(s): {', '.join(self.skipped_keys)}.")
        return " ".join(parts)


def split_by_prefix(
    store: ProfileStore,
    source_name: str,
    prefix_map: Dict[str, str],
    strip_prefix: bool = True,
    context: Optional[str] = None,
) -> SplitResult:
    """Split *source_name* into new profiles keyed by variable prefix.

    Args:
        store: The profile store to read from and write to.
        source_name: Name of the profile to split.
        prefix_map: Mapping of variable-name prefix -> new profile name.
        strip_prefix: When True, remove the prefix (and a trailing underscore)
            from the variable name in the destination profile.
        context: Override context for all created profiles.  Defaults to the
            source profile's context.

    Returns:
        A :class:`SplitResult` describing what was created.
    """
    source = store.get(source_name)
    if source is None:
        raise SplitError(f"Profile '{source_name}' not found.")

    buckets: Dict[str, Dict[str, str]] = {name: {} for name in prefix_map.values()}
    matched_keys: set[str] = set()

    for key, value in source.variables.items():
        for prefix, dest_name in prefix_map.items():
            if key.startswith(prefix):
                dest_key = key[len(prefix):].lstrip("_") if strip_prefix else key
                if not dest_key:
                    dest_key = key  # fallback: keep original if stripping yields empty
                buckets[dest_name][dest_key] = value
                matched_keys.add(key)
                break

    skipped = [k for k in source.variables if k not in matched_keys]
    result = SplitResult(source=source_name, skipped_keys=skipped)

    target_context = context or source.context
    for dest_name, variables in buckets.items():
        if not variables:
            continue
        dest_profile = Profile(
            name=dest_name,
            context=target_context,
            variables=variables,
        )
        store.add(dest_profile)
        result.created.append(dest_name)

    return result
