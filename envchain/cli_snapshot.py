"""CLI commands for managing profile snapshots."""

from pathlib import Path

import click

from envchain.profile import ProfileStore
from envchain.snapshot import Snapshot, SnapshotError, SnapshotStore

DEFAULT_STORE = Path.home() / ".envchain" / "profiles.json"
DEFAULT_SNAPSHOTS = Path.home() / ".envchain" / "snapshots.json"


@click.group()
def cli() -> None:
    """Snapshot management commands."""


@cli.command("create")
@click.argument("snapshot_name")
@click.option("--profile", "profiles", multiple=True, required=True,
              help="Profile name to include (repeatable).")
@click.option("--description", default="", help="Optional description.")
@click.option("--store", "store_path", default=str(DEFAULT_STORE), show_default=True)
@click.option("--snapshots", "snap_path", default=str(DEFAULT_SNAPSHOTS), show_default=True)
def create_command(
    snapshot_name: str,
    profiles: tuple,
    description: str,
    store_path: str,
    snap_path: str,
) -> None:
    """Create a snapshot of one or more profiles."""
    pstore = ProfileStore(Path(store_path))
    captured: dict = {}
    for pname in profiles:
        try:
            profile = pstore.get_profile(pname)
            captured[pname] = dict(profile.variables)
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc

    snap = Snapshot(name=snapshot_name, profiles=captured, description=description)
    sstore = SnapshotStore(Path(snap_path))
    try:
        sstore.save_snapshot(snap)
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Snapshot '{snapshot_name}' created with profiles: {', '.join(profiles)}.")


@cli.command("list")
@click.option("--snapshots", "snap_path", default=str(DEFAULT_SNAPSHOTS), show_default=True)
def list_command(snap_path: str) -> None:
    """List all saved snapshots."""
    sstore = SnapshotStore(Path(snap_path))
    snaps = sstore.list_snapshots()
    if not snaps:
        click.echo("No snapshots found.")
        return
    for snap in snaps:
        desc = f" — {snap.description}" if snap.description else ""
        click.echo(f"{snap.name}  [{snap.created_at}]{desc}")


@cli.command("delete")
@click.argument("snapshot_name")
@click.option("--snapshots", "snap_path", default=str(DEFAULT_SNAPSHOTS), show_default=True)
def delete_command(snapshot_name: str, snap_path: str) -> None:
    """Delete a snapshot by name."""
    sstore = SnapshotStore(Path(snap_path))
    try:
        sstore.delete_snapshot(snapshot_name)
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Snapshot '{snapshot_name}' deleted.")
