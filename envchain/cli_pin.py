"""CLI commands for profile pinning."""

from __future__ import annotations

import os
from pathlib import Path

import click

from envchain.pinning import PinStore, PinError


def _get_store() -> PinStore:
    base = Path(os.environ.get("ENVCHAIN_HOME", Path.home() / ".envchain"))
    base.mkdir(parents=True, exist_ok=True)
    return PinStore(base / "pins.json")


@click.group("pin")
def cli():
    """Manage profile snapshot pins."""


@cli.command("set")
@click.argument("profile")
@click.argument("snapshot_id")
@click.option("--note", default=None, help="Optional note for this pin.")
def set_command(profile: str, snapshot_id: str, note: str | None):
    """Pin PROFILE to SNAPSHOT_ID."""
    store = _get_store()
    entry = store.pin(profile, snapshot_id, note=note)
    click.echo(f"Pinned '{entry.profile_name}' to snapshot '{entry.snapshot_id}'.")


@cli.command("unset")
@click.argument("profile")
def unset_command(profile: str):
    """Remove the pin for PROFILE."""
    store = _get_store()
    try:
        store.unpin(profile)
        click.echo(f"Unpinned '{profile}'.")
    except PinError as exc:
        raise click.ClickException(str(exc))


@cli.command("show")
@click.argument("profile")
def show_command(profile: str):
    """Show the current pin for PROFILE."""
    store = _get_store()
    entry = store.get(profile)
    if entry is None:
        click.echo(f"Profile '{profile}' is not pinned.")
    else:
        note_part = f"  note: {entry.note}" if entry.note else ""
        click.echo(f"{entry.profile_name} -> {entry.snapshot_id}{note_part}")


@cli.command("list")
def list_command():
    """List all pinned profiles."""
    store = _get_store()
    pins = store.all_pins()
    if not pins:
        click.echo("No profiles are currently pinned.")
        return
    for entry in pins:
        note_part = f"  ({entry.note})" if entry.note else ""
        click.echo(f"{entry.profile_name} -> {entry.snapshot_id}{note_part}")
