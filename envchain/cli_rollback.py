"""CLI commands for rolling back profiles to previous history states."""

from __future__ import annotations

import click

from envchain.rollback import rollback_profile, list_rollback_points, RollbackError
from envchain.history import HistoryStore
from envchain.profile import ProfileStore


def _get_stores(env_dir: str):
    import os
    profile_path = os.path.join(env_dir, "profiles.json")
    history_path = os.path.join(env_dir, "history.json")
    return ProfileStore(profile_path), HistoryStore(history_path)


@click.group("rollback")
def cli():
    """Rollback profile variables to a previous state."""


@cli.command("list")
@click.argument("profile_name")
@click.option("--env-dir", default=".", show_default=True, help="Directory for data files.")
@click.option("--limit", default=10, show_default=True, help="Max entries to show.")
def list_command(profile_name: str, env_dir: str, limit: int):
    """List available rollback points for a profile."""
    _, history_store = _get_stores(env_dir)
    entries = list_rollback_points(profile_name, history_store, limit=limit)
    if not entries:
        click.echo(f"No history entries found for profile '{profile_name}'.")
        return
    click.echo(f"Rollback points for '{profile_name}':")
    for entry in entries:
        click.echo(f"  [{entry.id}] {entry.timestamp}  ({len(entry.variables)} vars)")


@cli.command("apply")
@click.argument("profile_name")
@click.argument("entry_id")
@click.option("--env-dir", default=".", show_default=True, help="Directory for data files.")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def apply_command(profile_name: str, entry_id: str, env_dir: str, yes: bool):
    """Restore a profile to a specific history entry."""
    profile_store, history_store = _get_stores(env_dir)
    if not yes:
        click.confirm(
            f"Rollback '{profile_name}' to entry '{entry_id}'? This will overwrite current variables.",
            abort=True,
        )
    try:
        result = rollback_profile(profile_name, entry_id, profile_store, history_store)
    except RollbackError as exc:
        raise click.ClickException(str(exc))

    if result.changed_keys:
        click.echo(f"Rolled back '{profile_name}' from entry '{entry_id}'.")
        click.echo(f"Changed keys: {', '.join(sorted(result.changed_keys))}")
    else:
        click.echo(f"Rolled back '{profile_name}' — no variable changes detected.")
