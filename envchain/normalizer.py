"""Normalize environment variable keys and values within a profile."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envchain.profile import Profile


class NormalizerError(Exception):
    """Raised when normalization encounters an unrecoverable problem."""


@dataclass
class NormalizeResult:
    profile: Profile
    renamed_keys: Dict[str, str] = field(default_factory=dict)  # old -> new
    stripped_keys: List[str] = field(default_factory=list)
    coerced_values: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.renamed_keys or self.stripped_keys or self.coerced_values)

    def summary(self) -> str:
        parts: List[str] = []
        if self.renamed_keys:
            parts.append(f"{len(self.renamed_keys)} key(s) uppercased")
        if self.stripped_keys:
            parts.append(f"{len(self.stripped_keys)} key(s) whitespace-stripped")
        if self.coerced_values:
            parts.append(f"{len(self.coerced_values)} value(s) whitespace-stripped")
        return "; ".join(parts) if parts else "no changes"


def normalize_profile(profile: Profile) -> NormalizeResult:
    """Return a new Profile with normalized keys and values.

    Normalization steps applied in order:
    1. Strip surrounding whitespace from keys.
    2. Uppercase keys.
    3. Strip surrounding whitespace from values.

    Duplicate keys produced after uppercasing cause a ``NormalizerError``.
    """
    renamed_keys: Dict[str, str] = {}
    stripped_keys: List[str] = []
    coerced_values: List[str] = []
    new_variables: Dict[str, str] = {}

    for raw_key, raw_value in profile.variables.items():
        # Step 1: strip whitespace from key
        stripped_key = raw_key.strip()
        if stripped_key != raw_key:
            stripped_keys.append(raw_key)

        # Step 2: uppercase key
        upper_key = stripped_key.upper()
        if upper_key != stripped_key:
            renamed_keys[raw_key] = upper_key

        if upper_key in new_variables:
            raise NormalizerError(
                f"Duplicate key '{upper_key}' produced during normalization."
            )

        # Step 3: strip whitespace from value
        stripped_value = raw_value.strip()
        if stripped_value != raw_value:
            coerced_values.append(upper_key)

        new_variables[upper_key] = stripped_value

    normalized = Profile(
        name=profile.name,
        context=profile.context,
        variables=new_variables,
    )
    return NormalizeResult(
        profile=normalized,
        renamed_keys=renamed_keys,
        stripped_keys=stripped_keys,
        coerced_values=coerced_values,
    )
