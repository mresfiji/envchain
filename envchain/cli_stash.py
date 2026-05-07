"""CLI commands for stashing and restoring profile variables."""
import click
from pathlib import Path

from envchain.profile import ProfileStore
from envchain.stasher import StashError, StashStore


def _get_stores(env_dir: str):
    base = Path(env_dir)
    base.mkdir(parents=True, exist_ok=True)
    profile_store = ProfileStore(base / "profiles.json")
    stash_store = StashStore(base / "stash.json")
    return profile_store, stash_store


@click.group("stash")
def cli():
    """Stash and restore profile variable snapshots."""


@cli.command("save")
@click.argument("label")
@click.argument("profile")
@click.option("--note", default=None, help="Optional note for this stash entry.")
@click.option("--env-dir", default=".envchain", envvar="ENVCHAIN_DIR")
def save_command(label: str, profile: str, note: str, env_dir: str):
    """Stash the current variables of PROFILE under LABEL."""
    profile_store, stash_store = _get_stores(env_dir)
    try:
        entry = stash_store.stash(label, profile_store, profile, note=note)
        click.echo(f"Stashed '{profile}' as '{entry.label}' ({len(entry.variables)} variables).")
    except StashError as exc:
        raise click.ClickException(str(exc))


@cli.command("pop")
@click.argument("label")
@click.option("--no-restore", is_flag=True, default=False, help="Discard stash without restoring.")
@click.option("--env-dir", default=".envchain", envvar="ENVCHAIN_DIR")
def pop_command(label: str, no_restore: bool, env_dir: str):
    """Pop stash LABEL and optionally restore variables to the profile."""
    profile_store, stash_store = _get_stores(env_dir)
    try:
        entry = stash_store.pop(label, profile_store, restore=not no_restore)
        action = "discarded" if no_restore else "restored"
        click.echo(f"Stash '{label}' {action} for profile '{entry.profile_name}'.")
    except StashError as exc:
        raise click.ClickException(str(exc))


@cli.command("list")
@click.option("--env-dir", default=".envchain", envvar="ENVCHAIN_DIR")
def list_command(env_dir: str):
    """List all stash entries."""
    _, stash_store = _get_stores(env_dir)
    entries = stash_store.list()
    if not entries:
        click.echo("No stash entries found.")
        return
    for entry in entries:
        note_str = f"  # {entry.note}" if entry.note else ""
        click.echo(f"{entry.label}  [{entry.profile_name}]  {len(entry.variables)} vars{note_str}")
