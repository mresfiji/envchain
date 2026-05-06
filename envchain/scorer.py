"""Profile quality scorer — assigns a numeric quality score to profiles."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envchain.profile import Profile


class ScorerError(Exception):
    """Raised when scoring fails."""


@dataclass
class ScoreBreakdown:
    category: str
    points: int
    max_points: int
    reason: str

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "points": self.points,
            "max_points": self.max_points,
            "reason": self.reason,
        }


@dataclass
class ScoreResult:
    profile_name: str
    total: int
    max_total: int
    grade: str
    breakdown: List[ScoreBreakdown] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        return round(self.total / self.max_total * 100, 1) if self.max_total else 0.0

    def summary(self) -> str:
        return (
            f"{self.profile_name}: {self.total}/{self.max_total} "
            f"({self.percentage}%) — Grade {self.grade}"
        )


def _grade(percentage: float) -> str:
    if percentage >= 90:
        return "A"
    if percentage >= 75:
        return "B"
    if percentage >= 60:
        return "C"
    if percentage >= 40:
        return "D"
    return "F"


def score_profile(profile: Profile) -> ScoreResult:
    """Score a profile and return a ScoreResult with breakdown."""
    breakdown: List[ScoreBreakdown] = []
    total = 0

    # 1. Non-empty profile (20 pts)
    if profile.variables:
        breakdown.append(ScoreBreakdown("non_empty", 20, 20, "Profile has variables"))
        total += 20
    else:
        breakdown.append(ScoreBreakdown("non_empty", 0, 20, "Profile has no variables"))

    # 2. No empty values (30 pts)
    empty_count = sum(1 for v in profile.variables.values() if v == "")
    if empty_count == 0:
        breakdown.append(ScoreBreakdown("no_empty_values", 30, 30, "All values are set"))
        total += 30
    else:
        pts = max(0, 30 - empty_count * 10)
        breakdown.append(ScoreBreakdown("no_empty_values", pts, 30, f"{empty_count} empty value(s)"))
        total += pts

    # 3. Valid context (20 pts)
    valid_contexts = {"local", "staging", "production"}
    if profile.context in valid_contexts:
        breakdown.append(ScoreBreakdown("valid_context", 20, 20, f"Context '{profile.context}' is recognised"))
        total += 20
    else:
        breakdown.append(ScoreBreakdown("valid_context", 0, 20, f"Unknown context '{profile.context}'"))

    # 4. Reasonable variable count (30 pts)
    count = len(profile.variables)
    if count >= 3:
        breakdown.append(ScoreBreakdown("variable_count", 30, 30, f"{count} variables defined"))
        total += 30
    elif count > 0:
        pts = count * 10
        breakdown.append(ScoreBreakdown("variable_count", pts, 30, f"Only {count} variable(s) defined"))
        total += pts
    else:
        breakdown.append(ScoreBreakdown("variable_count", 0, 30, "No variables defined"))

    max_total = 100
    grade = _grade(total / max_total * 100)
    return ScoreResult(
        profile_name=profile.name,
        total=total,
        max_total=max_total,
        grade=grade,
        breakdown=breakdown,
    )
