"""CLI commands for managing profile links."""
import click
from pathlib import Path
from envchain.linker import LinkStore, LinkError


def _get_store(env_dir: str) -> LinkStore:
    return LinkStore(Path(env_dir) / "links.json")


@click.group("link")
def cli() -> None:
    """Manage symbolic links between profiles."""


@cli.command("add")
@click.argument("source")
@click.argument("target")
@click.option("--note", default=None, help="Optional description for this link.")
@click.option("--env-dir", default=".", show_default=True, help="Directory with profile data.")
def add_command(source: str, target: str, note: str, env_dir: str) -> None:
    """Link SOURCE profile to TARGET so it inherits TARGET's variables."""
    store = _get_store(env_dir)
    try:
        entry = store.link(source, target, note=note)
        click.echo(f"Linked '{entry.source}' -> '{entry.target}'.")
        if entry.note:
            click.echo(f"Note: {entry.note}")
    except LinkError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@cli.command("remove")
@click.argument("source")
@click.option("--env-dir", default=".", show_default=True)
def remove_command(source: str, env_dir: str) -> None:
    """Remove the link from SOURCE profile."""
    store = _get_store(env_dir)
    try:
        store.unlink(source)
        click.echo(f"Unlinked '{source}'.")
    except LinkError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@cli.command("list")
@click.option("--env-dir", default=".", show_default=True)
def list_command(env_dir: str) -> None:
    """List all profile links."""
    store = _get_store(env_dir)
    entries = store.all_entries()
    if not entries:
        click.echo("No links defined.")
        return
    for entry in entries:
        note_part = f"  # {entry.note}" if entry.note else ""
        click.echo(f"  {entry.source} -> {entry.target}{note_part}")


@cli.command("chain")
@click.argument("source")
@click.option("--env-dir", default=".", show_default=True)
def chain_command(source: str, env_dir: str) -> None:
    """Show the full resolution chain for SOURCE profile."""
    store = _get_store(env_dir)
    chain = store.targets_for(source)
    if not chain:
        click.echo(f"'{source}' has no links.")
        return
    path = " -> ".join([source] + chain)
    click.echo(f"Chain: {path}")
