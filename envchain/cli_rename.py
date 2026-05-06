"""CLI command for renaming environment profiles."""

from __future__ import annotations

import click

from envchain.profile import ProfileStore
from envchain.renamer import RenameError, rename_profile


@click.group()
def cli() -> None:
    """Profile rename commands."""


@cli.command("run")
@click.argument("old_name")
@click.argument("new_name")
@click.option(
    "--context",
    "-c",
    default="local",
    show_default=True,
    help="Context in which the profile lives.",
)
@click.option(
    "--store",
    "store_path",
    default="profiles.json",
    show_default=True,
    envvar="ENVCHAIN_STORE",
    help="Path to the profile store file.",
)
@click.option(
    "--record-history",
    is_flag=True,
    default=False,
    help="Record the rename in the audit history.",
)
@click.option(
    "--history-store",
    "history_path",
    default="history.json",
    show_default=True,
    envvar="ENVCHAIN_HISTORY_STORE",
    help="Path to the history store file (used with --record-history).",
)
def rename_command(
    old_name: str,
    new_name: str,
    context: str,
    store_path: str,
    record_history: bool,
    history_path: str,
) -> None:
    """Rename OLD_NAME to NEW_NAME within the given context."""
    from pathlib import Path

    profile_store = ProfileStore(Path(store_path))

    history_store = None
    if record_history:
        from envchain.history import HistoryStore

        history_store = HistoryStore(Path(history_path))

    try:
        result = rename_profile(
            store=profile_store,
            old_name=old_name,
            new_name=new_name,
            context=context,
            history_store=history_store,
        )
    except RenameError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary())
