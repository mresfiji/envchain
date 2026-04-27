"""CLI commands for viewing and managing profile change history."""

from pathlib import Path

import click

from envchain.history import HistoryEntry, HistoryStore

DEFAULT_HISTORY_PATH = Path.home() / ".envchain" / "history.json"


def _get_store(history_file: str) -> HistoryStore:
    path = Path(history_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    return HistoryStore(path)


@click.group("history")
@click.option(
    "--history-file",
    default=str(DEFAULT_HISTORY_PATH),
    envvar="ENVCHAIN_HISTORY_FILE",
    show_default=True,
    help="Path to the history store.",
)
@click.pass_context
def cli(ctx: click.Context, history_file: str) -> None:
    """Manage profile change history."""
    ctx.ensure_object(dict)
    ctx.obj["history_file"] = history_file


@cli.command("list")
@click.argument("profile_name")
@click.pass_context
def list_command(ctx: click.Context, profile_name: str) -> None:
    """List history entries for a profile."""
    store = _get_store(ctx.obj["history_file"])
    entries = store.entries_for_profile(profile_name)
    if not entries:
        click.echo(f"No history found for profile '{profile_name}'.")
        return
    for entry in entries:
        note_str = f"  [{entry.note}]" if entry.note else ""
        click.echo(f"{entry.timestamp}  {entry.context}{note_str}")
        for k, v in entry.variables.items():
            click.echo(f"    {k}={v}")


@cli.command("record")
@click.argument("profile_name")
@click.argument("context")
@click.option("--var", "variables", multiple=True, metavar="KEY=VALUE",
              help="Variable to record (repeatable).")
@click.option("--note", default="", help="Optional note for this entry.")
@click.pass_context
def record_command(
    ctx: click.Context,
    profile_name: str,
    context: str,
    variables: tuple[str, ...],
    note: str,
) -> None:
    """Manually record a history entry for a profile."""
    parsed: dict[str, str] = {}
    for item in variables:
        if "=" not in item:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {item}")
        k, _, v = item.partition("=")
        parsed[k] = v
    store = _get_store(ctx.obj["history_file"])
    entry = HistoryEntry(profile_name=profile_name, context=context,
                         variables=parsed, note=note)
    store.record(entry)
    click.echo(f"Recorded history entry for '{profile_name}' ({context}).")


@cli.command("clear")
@click.argument("profile_name")
@click.pass_context
def clear_command(ctx: click.Context, profile_name: str) -> None:
    """Clear all history entries for a profile."""
    store = _get_store(ctx.obj["history_file"])
    removed = store.clear_profile(profile_name)
    click.echo(f"Removed {removed} history entry/entries for '{profile_name}'.")
