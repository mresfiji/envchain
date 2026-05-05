"""Watchdog module for monitoring profile variable drift against a baseline snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.profile import ProfileStore
from envchain.snapshot import SnapshotStore
from envchain.differ import diff_variables, DiffResult


class WatchdogError(Exception):
    """Raised when watchdog operations fail."""


@dataclass
class DriftReport:
    profile_name: str
    snapshot_label: str
    diff: DiffResult
    drifted: bool = field(init=False)

    def __post_init__(self) -> None:
        self.drifted = self.diff.has_changes()

    def summary(self) -> str:
        if not self.drifted:
            return f"[{self.profile_name}] No drift detected against snapshot '{self.snapshot_label}'."
        lines = [f"[{self.profile_name}] Drift detected against snapshot '{self.snapshot_label}':"]
        lines.append(self.diff.summary())
        return "\n".join(lines)


def check_drift(
    profile_name: str,
    snapshot_label: str,
    profile_store: ProfileStore,
    snapshot_store: SnapshotStore,
) -> DriftReport:
    """Compare the current profile variables against a named snapshot baseline."""
    profile = profile_store.get(profile_name)
    if profile is None:
        raise WatchdogError(f"Profile '{profile_name}' not found.")

    snapshot = snapshot_store.get(snapshot_label)
    if snapshot is None:
        raise WatchdogError(f"Snapshot '{snapshot_label}' not found.")

    baseline: Dict[str, str] = {}
    for snap_profile in snapshot.profiles:
        if snap_profile.name == profile_name:
            baseline = snap_profile.variables
            break

    diff = diff_variables(baseline, profile.variables)
    return DriftReport(profile_name=profile_name, snapshot_label=snapshot_label, diff=diff)


def check_all_drift(
    snapshot_label: str,
    profile_store: ProfileStore,
    snapshot_store: SnapshotStore,
) -> List[DriftReport]:
    """Check drift for all profiles captured in the given snapshot."""
    snapshot = snapshot_store.get(snapshot_label)
    if snapshot is None:
        raise WatchdogError(f"Snapshot '{snapshot_label}' not found.")

    reports: List[DriftReport] = []
    for snap_profile in snapshot.profiles:
        try:
            report = check_drift(
                snap_profile.name, snapshot_label, profile_store, snapshot_store
            )
            reports.append(report)
        except WatchdogError:
            pass
    return reports
