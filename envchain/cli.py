"""Main CLI entry point for envchain."""

from pathlib import Path

import click

from envchain.profile import Profile, ProfileStore
from envchain.resolver import ChainResolutionError, ProfileResolver
from envchain.exporter import export_variables
from envchain.cli_snapshot import cli as snapshot_cli

DEFAULT_STORE = Path.home() / ".envchain" / "profiles.json"


@click.group()
def cli() -> None:
    """envchain — manage and chain environment variable profiles."""


@cli.command("add")
@click.argument("name")
@click.argument("context", type=click.Choice(["local", "staging", "production"]))
@click.option("--var", "variables", multiple=True, metavar="KEY=VALUE",
              help="Variable in KEY=VALUE format (repeatable).")
@click.option("--store", "store_path", default=str(DEFAULT_STORE), show_default=True)
def add_command(name: str, context: str, variables: tuple, store_path: str) -> None:
    """Add or update a profile."""
    parsed: dict = {}
    for item in variables:
        if "=" not in item:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {item}")
        k, v = item.split("=", 1)
        parsed[k] = v
    store = ProfileStore(Path(store_path))
    profile = Profile(name=name, context=context, variables=parsed)
    store.add_profile(profile)
    click.echo(f"Profile '{name}' ({context}) saved with {len(parsed)} variable(s).")


@cli.command("list")
@click.option("--store", "store_path", default=str(DEFAULT_STORE), show_default=True)
def list_command(store_path: str) -> None:
    """List all profiles."""
    store = ProfileStore(Path(store_path))
    profiles = store.list_profiles()
    if not profiles:
        click.echo("No profiles found.")
        return
    for p in profiles:
        click.echo(f"{p.name}  [{p.context}]  {len(p.variables)} var(s)")


@cli.command("remove")
@click.argument("name")
@click.option("--store", "store_path", default=str(DEFAULT_STORE), show_default=True)
def remove_command(name: str, store_path: str) -> None:
    """Remove a profile by name."""
    store = ProfileStore(Path(store_path))
    store.remove_profile(name)
    click.echo(f"Profile '{name}' removed.")


@cli.command("resolve")
@click.argument("profiles", nargs=-1, required=True)
@click.option("--format", "fmt", type=click.Choice(["shell", "dotenv", "json"]),
              default="shell", show_default=True)
@click.option("--store", "store_path", default=str(DEFAULT_STORE), show_default=True)
def resolve_command(profiles: tuple, fmt: str, store_path: str) -> None:
    """Resolve and export merged variables from one or more profiles."""
    store = ProfileStore(Path(store_path))
    resolver = ProfileResolver(store)
    try:
        variables = resolver.resolve(list(profiles))
    except ChainResolutionError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(export_variables(variables, fmt))


@cli.command("export")
@click.argument("name")
@click.option("--format", "fmt", type=click.Choice(["shell", "dotenv", "json"]),
              default="shell", show_default=True)
@click.option("--store", "store_path", default=str(DEFAULT_STORE), show_default=True)
def export_command(name: str, fmt: str, store_path: str) -> None:
    """Export a single profile's variables."""
    store = ProfileStore(Path(store_path))
    resolver = ProfileResolver(store)
    try:
        variables = resolver.resolve_single(name)
    except ChainResolutionError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(export_variables(variables, fmt))


cli.add_command(snapshot_cli, name="snapshot")


if __name__ == "__main__":
    cli()
