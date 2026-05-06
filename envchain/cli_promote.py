"""CLI commands for profile promotion."""

from __future__ import annotations

import click

from envchain.profile import ProfileStore
from envchain.promoter import PromotionError, promote_profile


@click.group(name="promote")
def cli() -> None:
    """Promote a profile from one context to another."""


@cli.command(name="run")
@click.argument("profile_name")
@click.argument("target_context")
@click.option("--target-name", default=None, help="Override the name of the promoted profile.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite target if it already exists.")
@click.option("--store", "store_path", envvar="ENVCHAIN_STORE", default="profiles.json", show_default=True)
def promote_command(
    profile_name: str,
    target_context: str,
    target_name: str | None,
    overwrite: bool,
    store_path: str,
) -> None:
    """Promote PROFILE_NAME into TARGET_CONTEXT."""
    store = ProfileStore(store_path)
    try:
        result = promote_profile(
            store,
            source_name=profile_name,
            target_context=target_context,
            target_name=target_name,
            overwrite=overwrite,
        )
    except PromotionError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary())
