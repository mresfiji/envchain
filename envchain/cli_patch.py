"""CLI commands for patching profile variables."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from envchain.profile import ProfileStore
from envchain.patcher import PatchError, patch_profile


def _get_store(env_dir: str) -> ProfileStore:
    return ProfileStore(Path(env_dir) / "profiles.json")


@click.group()
def cli() -> None:
    """Patch variables inside a profile."""


@cli.command("run")
@click.argument("profile_name")
@click.argument("assignments", nargs=-1, required=True, metavar="KEY=VALUE...")
@click.option("--add-missing", is_flag=True, default=False, help="Add keys that do not exist yet.")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without saving.")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.option("--env-dir", default=".", show_default=True, help="Directory containing profiles.json.")
def run_command(
    profile_name: str,
    assignments: tuple,
    add_missing: bool,
    dry_run: bool,
    output_format: str,
    env_dir: str,
) -> None:
    """Patch KEY=VALUE pairs into PROFILE_NAME."""
    patches: dict[str, str] = {}
    for assignment in assignments:
        if "=" not in assignment:
            click.echo(f"Error: invalid assignment '{assignment}' — expected KEY=VALUE.", err=True)
            sys.exit(1)
        key, _, value = assignment.partition("=")
        patches[key.strip()] = value

    store = _get_store(env_dir)
    try:
        result = patch_profile(
            store, profile_name, patches, add_missing=add_missing, dry_run=dry_run
        )
    except PatchError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if output_format == "json":
        click.echo(
            json.dumps(
                {
                    "profile": result.profile_name,
                    "applied": result.applied,
                    "skipped": result.skipped,
                    "previous": result.previous,
                    "dry_run": dry_run,
                },
                indent=2,
            )
        )
    else:
        prefix = "[dry-run] " if dry_run else ""
        click.echo(f"{prefix}{result.summary()}")
        for key, new_val in result.applied.items():
            old_val = result.previous.get(key, "")
            click.echo(f"  {key}: {old_val!r} -> {new_val!r}")
        for key in result.skipped:
            click.echo(f"  {key}: skipped (not found)")
