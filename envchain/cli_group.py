"""CLI commands for profile grouping."""
from __future__ import annotations

import os
from pathlib import Path

import click

from envchain.grouper import GroupIndex, GroupError, load_index, save_index


def _index_path() -> Path:
    return Path(os.environ.get("ENVCHAIN_GROUP_INDEX", ".envchain_groups.json"))


@click.group("group")
def cli() -> None:
    """Manage profile groups."""


@cli.command("add")
@click.argument("group")
@click.argument("profile")
def add_command(group: str, profile: str) -> None:
    """Add PROFILE to GROUP."""
    path = _index_path()
    index = load_index(path)
    try:
        index.add(group, profile)
    except GroupError as exc:
        raise click.ClickException(str(exc))
    save_index(index, path)
    click.echo(f"Added '{profile}' to group '{group}'.")


@cli.command("remove")
@click.argument("group")
@click.argument("profile")
def remove_command(group: str, profile: str) -> None:
    """Remove PROFILE from GROUP."""
    path = _index_path()
    index = load_index(path)
    try:
        index.remove(group, profile)
    except GroupError as exc:
        raise click.ClickException(str(exc))
    save_index(index, path)
    click.echo(f"Removed '{profile}' from group '{group}'.")


@cli.command("list")
@click.argument("group")
def list_command(group: str) -> None:
    """List profiles in GROUP."""
    index = load_index(_index_path())
    members = index.profiles_for_group(group)
    if not members:
        click.echo(f"Group '{group}' is empty or does not exist.")
        return
    for profile in members:
        click.echo(profile)


@cli.command("show")
@click.argument("profile")
def show_command(profile: str) -> None:
    """Show all groups that PROFILE belongs to."""
    index = load_index(_index_path())
    groups = index.groups_for_profile(profile)
    if not groups:
        click.echo(f"Profile '{profile}' does not belong to any group.")
        return
    for g in groups:
        click.echo(g)
