"""Profile linter for detecting common issues in environment variable profiles."""

from dataclasses import dataclass, field
from typing import List, Optional
from envchain.profile import Profile


@dataclass
class LintIssue:
    level: str  # 'error' | 'warning' | 'info'
    code: str
    message: str
    variable: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "variable": self.variable,
        }


@dataclass
class LintResult:
    profile_name: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.level == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.level == "warning" for i in self.issues)

    def summary(self) -> str:
        errors = sum(1 for i in self.issues if i.level == "error")
        warnings = sum(1 for i in self.issues if i.level == "warning")
        return f"{self.profile_name}: {errors} error(s), {warnings} warning(s)"


_SENSITIVE_PATTERNS = ("SECRET", "PASSWORD", "TOKEN", "KEY", "PRIVATE", "CREDENTIAL")
_PLACEHOLDER_PATTERNS = ("CHANGEME", "TODO", "FIXME", "PLACEHOLDER", "EXAMPLE", "REPLACE")


def lint_profile(profile: Profile) -> LintResult:
    result = LintResult(profile_name=profile.name)

    if not profile.variables:
        result.issues.append(LintIssue(
            level="warning",
            code="W001",
            message="Profile has no variables defined.",
        ))
        return result

    for name, value in profile.variables.items():
        upper_name = name.upper()
        upper_value = value.upper() if value else ""

        if value == "":
            result.issues.append(LintIssue(
                level="warning",
                code="W002",
                message=f"Variable '{name}' has an empty value.",
                variable=name,
            ))

        if any(pat in upper_name for pat in _SENSITIVE_PATTERNS) and len(value) < 8:
            result.issues.append(LintIssue(
                level="error",
                code="E001",
                message=f"Sensitive variable '{name}' appears to have a weak or short value.",
                variable=name,
            ))

        if any(pat in upper_value for pat in _PLACEHOLDER_PATTERNS):
            result.issues.append(LintIssue(
                level="error",
                code="E002",
                message=f"Variable '{name}' looks like a placeholder value: '{value}'.",
                variable=name,
            ))

        if value and (value.startswith(" ") or value.endswith(" ")):
            result.issues.append(LintIssue(
                level="warning",
                code="W003",
                message=f"Variable '{name}' has leading or trailing whitespace.",
                variable=name,
            ))

    return result
