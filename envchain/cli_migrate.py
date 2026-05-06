"""CLI commands for key-rename migrations across profiles."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import click

from envchain.profile import ProfileStore
from envchain.migrator import MigrationError, migrate_profile, migrate_all


@click.group(name="migrate")
def cli() -> None:
    """Rename environment variable keys within profiles."""


@cli.command(name="run")
@click.argument("profile")
@click.option(
    "--rename",
    "renames",
    multiple=True,
    metavar="OLD=NEW",
    required=True,
    help="Key rename pair, e.g. DB_HOST=DATABASE_HOST. Repeatable.",
)
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing target keys.")
@click.option("--store", "store_path", envvar="ENVCHAIN_STORE", default="envchain_store.json", show_default=True)
def run_command(profile: str, renames: tuple, overwrite: bool, store_path: str) -> None:
    """Rename keys in a single PROFILE."""
    key_map = _parse_renames(renames)
    store = ProfileStore(Path(store_path))
    try:
        result = migrate_profile(store, profile, key_map, overwrite=overwrite)
    except MigrationError as exc:
        raise click.ClickException(str(exc))
    click.echo(result.summary())


@cli.command(name="run-all")
@click.option(
    "--rename",
    "renames",
    multiple=True,
    metavar="OLD=NEW",
    required=True,
    help="Key rename pair. Repeatable.",
)
@click.option("--context", default=None, help="Limit migration to profiles with this context.")
@click.option("--overwrite", is_flag=True, default=False)
@click.option("--store", "store_path", envvar="ENVCHAIN_STORE", default="envchain_store.json", show_default=True)
def run_all_command(
    renames: tuple,
    context: Optional[str],
    overwrite: bool,
    store_path: str,
) -> None:
    """Rename keys across ALL profiles (optionally filtered by --context)."""
    key_map = _parse_renames(renames)
    store = ProfileStore(Path(store_path))
    try:
        results = migrate_all(store, key_map, context=context, overwrite=overwrite)
    except MigrationError as exc:
        raise click.ClickException(str(exc))
    for result in results:
        click.echo(result.summary())
    changed = sum(1 for r in results if r.has_changes)
    click.echo(f"\n{changed}/{len(results)} profile(s) updated.")


def _parse_renames(renames: tuple) -> dict:
    key_map: dict = {}
    for pair in renames:
        if "=" not in pair:
            raise click.BadParameter(f"Invalid rename pair '{pair}': expected OLD=NEW format.")
        old, new = pair.split("=", 1)
        old, new = old.strip(), new.strip()
        if not old or not new:
            raise click.BadParameter(f"Empty key in rename pair '{pair}'.")
        key_map[old] = new
    return key_map
