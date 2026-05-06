"""CLI commands for variable interpolation within profiles."""

from __future__ import annotations

import json
import os

import click

from envchain.interpolator import InterpolationError, interpolate_profile
from envchain.profile import ProfileStore


def _get_store() -> ProfileStore:
    path = os.environ.get("ENVCHAIN_STORE", "envchain_store.json")
    return ProfileStore(path)


@click.group("interpolate")
def cli() -> None:
    """Interpolate variable references within a profile."""


@cli.command("run")
@click.argument("profile_name")
@click.option("--context", "ctx_name", default=None, help="Context filter (e.g. local, staging).")
@click.option("--strict", is_flag=True, default=False, help="Fail if any references are unresolved.")
@click.option("--format", "fmt", type=click.Choice(["shell", "json", "dotenv"]), default="shell")
def run_command(profile_name: str, ctx_name: str | None, strict: bool, fmt: str) -> None:
    """Interpolate and print resolved variables for PROFILE_NAME."""
    store = _get_store()
    profile = store.get(profile_name)
    if profile is None:
        raise click.ClickException(f"Profile '{profile_name}' not found.")
    if ctx_name and profile.context != ctx_name:
        raise click.ClickException(
            f"Profile context '{profile.context}' does not match '{ctx_name}'."
        )

    try:
        result = interpolate_profile(profile, strict=strict)
    except InterpolationError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.has_unresolved:
        click.echo(
            click.style(
                f"Warning: unresolved references: {', '.join(result.unresolved)}",
                fg="yellow",
            ),
            err=True,
        )

    if fmt == "shell":
        for key, val in sorted(result.resolved.items()):
            click.echo(f"export {key}={val!r}")
    elif fmt == "dotenv":
        for key, val in sorted(result.resolved.items()):
            click.echo(f"{key}={val}")
    elif fmt == "json":
        click.echo(json.dumps(result.resolved, indent=2, sort_keys=True))

    click.echo(
        click.style(f"# {result.summary()}", fg="cyan"),
        err=True,
    )
