"""Profile model and storage management for envchain."""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_STORE_PATH = Path.home() / ".envchain" / "profiles.json"


@dataclass
class Profile:
    name: str
    context: str  # local | staging | production
    vars: Dict[str, str] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        return cls(
            name=data["name"],
            context=data["context"],
            vars=data.get("vars", {}),
            description=data.get("description", ""),
        )


class ProfileStore:
    VALID_CONTEXTS = {"local", "staging", "production"}

    def __init__(self, store_path: Path = DEFAULT_STORE_PATH):
        self.store_path = store_path
        self._profiles: Dict[str, Profile] = {}
        self._load()

    def _load(self) -> None:
        if self.store_path.exists():
            with open(self.store_path, "r") as f:
                raw = json.load(f)
            self._profiles = {
                name: Profile.from_dict(data)
                for name, data in raw.items()
            }

    def _save(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.store_path, "w") as f:
            json.dump(
                {name: p.to_dict() for name, p in self._profiles.items()},
                f,
                indent=2,
            )

    def add(self, profile: Profile) -> None:
        if profile.context not in self.VALID_CONTEXTS:
            raise ValueError(
                f"Invalid context '{profile.context}'. "
                f"Choose from: {', '.join(sorted(self.VALID_CONTEXTS))}"
            )
        self._profiles[profile.name] = profile
        self._save()

    def get(self, name: str) -> Optional[Profile]:
        return self._profiles.get(name)

    def remove(self, name: str) -> bool:
        if name in self._profiles:
            del self._profiles[name]
            self._save()
            return True
        return False

    def list_all(self) -> List[Profile]:
        return list(self._profiles.values())

    def list_by_context(self, context: str) -> List[Profile]:
        return [p for p in self._profiles.values() if p.context == context]
