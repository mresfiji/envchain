"""CLI commands for managing profile labels."""
from __future__ import annotations

import click
from pathlib import Path
from envchain.labeler import LabelError, LabelIndex


def _index_path(env_dir: str) -> Path:
    return Path(env_dir) / "labels.json"


@click.group("label")
def cli() -> None:
    """Manage free-form labels on profiles."""


@cli.command("add")
@click.argument("profile")
@click.argument("label")
@click.option("--env-dir", default=".envchain", show_default=True)
def add_command(profile: str, label: str, env_dir: str) -> None:
    """Attach LABEL to PROFILE."""
    path = _index_path(env_dir)
    idx = LabelIndex.load(path)
    try:
        idx.add(profile, label)
    except LabelError as exc:
        raise click.ClickException(str(exc))
    idx.save(path)
    click.echo(f"Label '{label}' added to profile '{profile}'.")


@cli.command("remove")
@click.argument("profile")
@click.argument("label")
@click.option("--env-dir", default=".envchain", show_default=True)
def remove_command(profile: str, label: str, env_dir: str) -> None:
    """Remove LABEL from PROFILE."""
    path = _index_path(env_dir)
    idx = LabelIndex.load(path)
    try:
        idx.remove(profile, label)
    except LabelError as exc:
        raise click.ClickException(str(exc))
    idx.save(path)
    click.echo(f"Label '{label}' removed from profile '{profile}'.")


@cli.command("list")
@click.argument("profile")
@click.option("--env-dir", default=".envchain", show_default=True)
def list_command(profile: str, env_dir: str) -> None:
    """List all labels attached to PROFILE."""
    idx = LabelIndex.load(_index_path(env_dir))
    labels = idx.labels_for_profile(profile)
    if not labels:
        click.echo(f"No labels for profile '{profile}'.")
    else:
        for label in labels:
            click.echo(label)


@cli.command("find")
@click.argument("label")
@click.option("--env-dir", default=".envchain", show_default=True)
def find_command(label: str, env_dir: str) -> None:
    """Find all profiles that carry LABEL."""
    idx = LabelIndex.load(_index_path(env_dir))
    profiles = idx.profiles_for_label(label)
    if not profiles:
        click.echo(f"No profiles found with label '{label}'.")
    else:
        for profile in profiles:
            click.echo(profile)
