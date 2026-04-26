"""Profile merging utilities for combining multiple profiles into one."""

from typing import List, Dict, Optional
from envchain.profile import Profile


class MergeError(Exception):
    """Raised when a profile merge operation fails."""


MergeStrategy = str
STRATEGY_LAST_WINS = "last_wins"
STRATEGY_FIRST_WINS = "first_wins"
STRATEGY_ERROR_ON_CONFLICT = "error_on_conflict"

VALID_STRATEGIES = {STRATEGY_LAST_WINS, STRATEGY_FIRST_WINS, STRATEGY_ERROR_ON_CONFLICT}


def merge_profiles(
    profiles: List[Profile],
    strategy: MergeStrategy = STRATEGY_LAST_WINS,
    output_name: str = "merged",
    output_context: str = "local",
) -> Profile:
    """Merge multiple profiles into a single profile.

    Args:
        profiles: Ordered list of profiles to merge.
        strategy: How to handle conflicting keys.
        output_name: Name for the resulting merged profile.
        output_context: Context for the resulting merged profile.

    Returns:
        A new Profile containing merged variables.

    Raises:
        MergeError: If strategy is invalid or a conflict is detected with error_on_conflict.
    """
    if strategy not in VALID_STRATEGIES:
        raise MergeError(
            f"Invalid merge strategy '{strategy}'. "
            f"Choose from: {', '.join(sorted(VALID_STRATEGIES))}"
        )

    if not profiles:
        return Profile(name=output_name, context=output_context, variables={})

    merged: Dict[str, str] = {}
    seen_in: Dict[str, str] = {}  # key -> profile name where first seen

    for profile in profiles:
        for key, value in profile.variables.items():
            if key in merged:
                if strategy == STRATEGY_ERROR_ON_CONFLICT:
                    raise MergeError(
                        f"Conflict: key '{key}' exists in both "
                        f"'{seen_in[key]}' and '{profile.name}'."
                    )
                elif strategy == STRATEGY_FIRST_WINS:
                    continue  # keep existing value
                else:  # last_wins
                    merged[key] = value
                    seen_in[key] = profile.name
            else:
                merged[key] = value
                seen_in[key] = profile.name

    return Profile(name=output_name, context=output_context, variables=merged)


def diff_merge_preview(
    profiles: List[Profile],
    strategy: MergeStrategy = STRATEGY_LAST_WINS,
) -> Dict[str, Dict]:
    """Return a preview of which profile each key will come from after merging."""
    if strategy not in VALID_STRATEGIES:
        raise MergeError(f"Invalid merge strategy '{strategy}'.")

    result: Dict[str, Dict] = {}

    for profile in profiles:
        for key, value in profile.variables.items():
            if key not in result:
                result[key] = {"value": value, "source": profile.name, "overridden_by": None}
            else:
                if strategy == STRATEGY_LAST_WINS:
                    result[key]["overridden_by"] = profile.name
                    result[key]["value"] = value
                    result[key]["source"] = profile.name

    return result
