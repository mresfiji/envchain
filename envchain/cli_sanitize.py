"""CLI commands for sanitizing profile output."""

from __future__ import annotations

import json
import os

import click

from envchain.profile import ProfileStore
from envchain.sanitizer import SanitizerError, sanitize_profile


@click.group("sanitize")
def cli() -> None:
    """Sanitize sensitive variable values in a profile."""


@cli.command("show")
@click.argument("profile_name")
@click.option(
    "--mode",
    type=click.Choice(["redact", "mask"]),
    default="redact",
    show_default=True,
    help="How to handle sensitive values.",
)
@click.option(
    "--extra-key",
    "extra_keys",
    multiple=True,
    help="Additional key names to treat as sensitive (repeatable).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
)
@click.option("--store", "store_path", default=None, help="Path to profile store file.")
def show_command(
    profile_name: str,
    mode: str,
    extra_keys: tuple,
    output_format: str,
    store_path: str | None,
) -> None:
    """Display a profile with sensitive values sanitized."""
    path = store_path or os.environ.get("ENVCHAIN_STORE", "envchain_store.json")
    store = ProfileStore(path)

    profile = store.get(profile_name)
    if profile is None:
        raise click.ClickException(f"Profile {profile_name!r} not found.")

    try:
        result = sanitize_profile(profile, mode=mode, extra_keys=list(extra_keys))
    except SanitizerError as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        click.echo(
            json.dumps(
                {
                    "profile": result.original_name,
                    "variables": result.sanitized_variables,
                    "redacted_keys": sorted(result.redacted_keys),
                    "masked_keys": sorted(result.masked_keys),
                },
                indent=2,
            )
        )
    else:
        click.echo(f"Profile: {result.original_name}")
        for key, value in sorted(result.sanitized_variables.items()):
            click.echo(f"  {key}={value}")
        click.echo(result.summary())
