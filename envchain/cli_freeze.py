"""CLI commands for freezing and unfreezing profiles."""

from __future__ import annotations

import os
from pathlib import Path

import click

from envchain.freezer import FreezeError, FreezeStore
from envchain.profile import ProfileStore


def _get_stores(env_dir: str):
    base = Path(env_dir)
    profile_store = ProfileStore(base / "profiles.json")
    freeze_store = FreezeStore(base / "freeze_index.json")
    return profile_store, freeze_store


@click.group("freeze")
def cli():
    """Freeze or unfreeze environment profiles."""


@cli.command("lock")
@click.argument("profile_name")
@click.option("--reason", default=None, help="Reason for freezing.")
@click.option("--env-dir", default=lambda: os.environ.get("ENVCHAIN_DIR", ".envchain"))
def lock_command(profile_name: str, reason: str, env_dir: str):
    """Freeze a profile, preventing further modifications."""
    profile_store, freeze_store = _get_stores(env_dir)
    try:
        profile = profile_store.get_profile(profile_name)
    except Exception:
        raise click.ClickException(f"Profile '{profile_name}' not found.")
    try:
        entry = freeze_store.freeze(
            profile_name=profile_name,
            context=profile.context,
            variables=profile.variables,
            reason=reason,
        )
        click.echo(f"Profile '{profile_name}' frozen ({entry.context}).")
        if reason:
            click.echo(f"Reason: {reason}")
    except FreezeError as exc:
        raise click.ClickException(str(exc))


@cli.command("unlock")
@click.argument("profile_name")
@click.option("--env-dir", default=lambda: os.environ.get("ENVCHAIN_DIR", ".envchain"))
def unlock_command(profile_name: str, env_dir: str):
    """Unfreeze a previously frozen profile."""
    _, freeze_store = _get_stores(env_dir)
    try:
        freeze_store.unfreeze(profile_name)
        click.echo(f"Profile '{profile_name}' unfrozen.")
    except FreezeError as exc:
        raise click.ClickException(str(exc))


@cli.command("list")
@click.option("--env-dir", default=lambda: os.environ.get("ENVCHAIN_DIR", ".envchain"))
def list_command(env_dir: str):
    """List all frozen profiles."""
    _, freeze_store = _get_stores(env_dir)
    entries = freeze_store.list_frozen()
    if not entries:
        click.echo("No frozen profiles.")
        return
    for entry in entries:
        reason_str = f" — {entry.reason}" if entry.reason else ""
        click.echo(f"  {entry.profile_name} [{entry.context}]{reason_str}")
