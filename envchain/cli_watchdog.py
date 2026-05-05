"""CLI commands for the envchain watchdog (drift detection) feature."""

import click
from pathlib import Path

from envchain.profile import ProfileStore
from envchain.snapshot import SnapshotStore
from envchain.watchdog import check_drift, check_all_drift, WatchdogError


def _get_stores(env_dir: Path):
    profile_store = ProfileStore(env_dir / "profiles.json")
    snapshot_store = SnapshotStore(env_dir / "snapshots.json")
    return profile_store, snapshot_store


@click.group(name="watchdog")
def cli():
    """Monitor profile drift against snapshot baselines."""


@cli.command(name="check")
@click.argument("profile_name")
@click.argument("snapshot_label")
@click.option("--env-dir", default=".envchain", show_default=True, help="Storage directory.")
@click.option("--fail-on-drift", is_flag=True, default=False, help="Exit with code 1 if drift detected.")
def check_command(profile_name: str, snapshot_label: str, env_dir: str, fail_on_drift: bool):
    """Check a single profile for drift against a snapshot."""
    profile_store, snapshot_store = _get_stores(Path(env_dir))
    try:
        report = check_drift(profile_name, snapshot_label, profile_store, snapshot_store)
    except WatchdogError as exc:
        raise click.ClickException(str(exc))

    click.echo(report.summary())
    if fail_on_drift and report.drifted:
        raise SystemExit(1)


@cli.command(name="check-all")
@click.argument("snapshot_label")
@click.option("--env-dir", default=".envchain", show_default=True, help="Storage directory.")
@click.option("--fail-on-drift", is_flag=True, default=False, help="Exit with code 1 if any drift detected.")
def check_all_command(snapshot_label: str, env_dir: str, fail_on_drift: bool):
    """Check all profiles in a snapshot for drift."""
    profile_store, snapshot_store = _get_stores(Path(env_dir))
    try:
        reports = check_all_drift(snapshot_label, profile_store, snapshot_store)
    except WatchdogError as exc:
        raise click.ClickException(str(exc))

    if not reports:
        click.echo("No profiles found in snapshot.")
        return

    any_drift = False
    for report in reports:
        click.echo(report.summary())
        if report.drifted:
            any_drift = True

    if fail_on_drift and any_drift:
        raise SystemExit(1)
