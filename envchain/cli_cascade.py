"""CLI commands for cascading environment variable profiles."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import click

from envchain.cascader import CascadeError, cascade_profiles
from envchain.exporter import export_variables
from envchain.profile import ProfileStore


def _get_store(env_dir: str) -> ProfileStore:
    return ProfileStore(Path(env_dir) / "profiles.json")


@click.group("cascade")
def cli() -> None:
    """Cascade and merge profiles in order."""


@cli.command("run")
@click.argument("profiles", nargs=-1, required=True)
@click.option("--env-dir", default=".envchain", envvar="ENVCHAIN_DIR", show_default=True)
@click.option("--format", "fmt", type=click.Choice(["shell", "dotenv", "json"]), default="shell", show_default=True)
@click.option("--output", "-o", default=None, help="Write output to file instead of stdout.")
@click.option("--show-provenance", is_flag=True, default=False, help="Print key provenance after output.")
def run_command(
    profiles: tuple,
    env_dir: str,
    fmt: str,
    output: Optional[str],
    show_provenance: bool,
) -> None:
    """Cascade PROFILES left-to-right and emit merged variables."""
    store = _get_store(env_dir)
    try:
        result = cascade_profiles(list(profiles), store)
    except CascadeError as exc:
        raise click.ClickException(str(exc)) from exc

    rendered = export_variables(result.merged_variables, fmt)

    if output:
        Path(output).write_text(rendered)
        click.echo(f"Written to {output}")
    else:
        click.echo(rendered)

    if show_provenance:
        click.echo("\n# Provenance:", err=True)
        for key, src in sorted(result.override_map.items()):
            click.echo(f"#   {key} <- {src}", err=True)


@cli.command("summary")
@click.argument("profiles", nargs=-1, required=True)
@click.option("--env-dir", default=".envchain", envvar="ENVCHAIN_DIR", show_default=True)
def summary_command(profiles: tuple, env_dir: str) -> None:
    """Print a summary of the cascade result without exporting."""
    store = _get_store(env_dir)
    try:
        result = cascade_profiles(list(profiles), store)
    except CascadeError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary())
