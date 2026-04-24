"""Resolves and chains environment variable profiles."""

from typing import Dict, List, Optional
from envchain.profile import Profile, ProfileStore


class ChainResolutionError(Exception):
    """Raised when a profile chain cannot be resolved."""
    pass


class ProfileResolver:
    """Resolves environment variables by chaining multiple profiles.

    Profiles are resolved in order, with later profiles overriding
    earlier ones for duplicate keys.
    """

    def __init__(self, store: ProfileStore):
        self.store = store

    def resolve(self, profile_names: List[str], context: str = "local") -> Dict[str, str]:
        """Resolve environment variables from a chain of profiles.

        Args:
            profile_names: Ordered list of profile names to chain.
            context: The context to resolve profiles in.

        Returns:
            Merged dictionary of environment variables.

        Raises:
            ChainResolutionError: If a profile is not found.
        """
        merged: Dict[str, str] = {}

        for name in profile_names:
            profile = self.store.get_profile(name, context)
            if profile is None:
                raise ChainResolutionError(
                    f"Profile '{name}' not found in context '{context}'."
                )
            merged.update(profile.variables)

        return merged

    def resolve_single(self, profile_name: str, context: str = "local") -> Dict[str, str]:
        """Resolve a single profile by name and context."""
        return self.resolve([profile_name], context)

    def list_chain(self, profile_names: List[str], context: str = "local") -> List[Profile]:
        """Return the list of Profile objects for a given chain.

        Raises:
            ChainResolutionError: If any profile is missing.
        """
        profiles = []
        for name in profile_names:
            profile = self.store.get_profile(name, context)
            if profile is None:
                raise ChainResolutionError(
                    f"Profile '{name}' not found in context '{context}'."
                )
            profiles.append(profile)
        return profiles
