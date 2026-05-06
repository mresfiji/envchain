"""Broadcast resolved environment variables to multiple export targets simultaneously."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envchain.exporter import export_variables, ExportFormatError


class BroadcastError(Exception):
    """Raised when a broadcast operation fails."""


@dataclass
class BroadcastTarget:
    format: str  # 'shell', 'dotenv', or 'json'
    path: Path
    label: Optional[str] = None

    def __post_init__(self) -> None:
        if self.format not in ("shell", "dotenv", "json"):
            raise BroadcastError(f"Unsupported broadcast format: {self.format!r}")


@dataclass
class BroadcastResult:
    succeeded: List[str] = field(default_factory=list)
    failed: Dict[str, str] = field(default_factory=dict)

    @property
    def has_failures(self) -> bool:
        return bool(self.failed)

    def summary(self) -> str:
        lines = [f"Broadcast complete: {len(self.succeeded)} succeeded, {len(self.failed)} failed."]
        for label, reason in self.failed.items():
            lines.append(f"  FAILED [{label}]: {reason}")
        return "\n".join(lines)


def broadcast(
    variables: Dict[str, str],
    targets: List[BroadcastTarget],
) -> BroadcastResult:
    """Write *variables* to every target, collecting successes and failures."""
    if not targets:
        raise BroadcastError("No broadcast targets provided.")

    result = BroadcastResult()

    for target in targets:
        label = target.label or str(target.path)
        try:
            content = export_variables(variables, target.format)
            target.path.parent.mkdir(parents=True, exist_ok=True)
            target.path.write_text(content, encoding="utf-8")
            result.succeeded.append(label)
        except ExportFormatError as exc:
            result.failed[label] = f"Export error: {exc}"
        except OSError as exc:
            result.failed[label] = f"I/O error: {exc}"

    return result
