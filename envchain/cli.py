"""Main CLI entry point for envchain.

Provides the top-level command group and registers all subcommands
for managing environment variable profiles.
"""

import sys
import click

from envchain.profile import ProfileStore
from envchain.resolver import ProfileResolver
from envchain.exporter import export_variables
from envchain.importer import import_from_dotenv_file, import_from_environment
from envchain.validator import ValidationError, validate_profile_name, validate_variables
from envchain.audit import AuditLog
from envchain import __version__


DEFAULT_STORE_PATH = ".envchain/profiles.json"
DEFAULT_AUDIT_PATH = ".envchain/audit.log"


@click.group()
@click.version_option(version=__version__, prog_name="envchain")
@click.option(
    "--store",
    default=DEFAULT_STORE_PATH,
    envvar="ENVCHAIN_STORE",
    show_default=True,
    help="Path to the profile store file.",
)
@click.pass_context
def cli(ctx: click.Context, store: str) -> None:
    """envchain — manage and chain environment variable profiles."""
    ctx.ensure_object(dict)
    ctx.obj["store"] = ProfileStore(store)
    ctx.obj["audit"] = AuditLog(DEFAULT_AUDIT_PATH)


@cli.command("add")
@click.argument("profile_name")
@click.argument("context", type=click.Choice(["local", "staging", "production"]))
@click.option("-e", "--env", "pairs", multiple=True, metavar="KEY=VALUE",
              help="Environment variable in KEY=VALUE format.")
@click.option("--from-dotenv", "dotenv_file", default=None,
              help="Import variables from a .env file.")
@click.option("--from-environment", "env_prefix", default=None,
              help="Import variables from the current environment matching a prefix.")
@click.pass_context
def add_command(
    ctx: click.Context,
    profile_name: str,
    context: str,
    pairs: tuple,
    dotenv_file: str,
    env_prefix: str,
) -> None:
    """Add or update a profile with environment variables."""
    store: ProfileStore = ctx.obj["store"]
    audit: AuditLog = ctx.obj["audit"]

    variables: dict = {}

    # Collect variables from --env flags
    for pair in pairs:
        if "=" not in pair:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {pair!r}", param_hint="--env")
        key, _, value = pair.partition("=")
        variables[key] = value

    # Merge variables from .env file
    if dotenv_file:
        try:
            variables.update(import_from_dotenv_file(dotenv_file))
        except Exception as exc:  # noqa: BLE001
            raise click.ClickException(str(exc)) from exc

    # Merge variables from current environment by prefix
    if env_prefix:
        variables.update(import_from_environment(env_prefix))

    if not variables:
        raise click.ClickException("No variables provided. Use --env, --from-dotenv, or --from-environment.")

    try:
        validate_profile_name(profile_name)
        validate_variables(variables)
    except ValidationError as exc:
        raise click.ClickException(str(exc)) from exc

    store.add_profile(profile_name, context, variables)
    audit.record("add", profile_name, details={"context": context, "keys": list(variables.keys())})
    click.echo(f"Profile '{profile_name}' ({context}) saved with {len(variables)} variable(s).")


@cli.command("list")
@click.pass_context
def list_command(ctx: click.Context) -> None:
    """List all stored profiles."""
    store: ProfileStore = ctx.obj["store"]
    profiles = store.all_profiles()

    if not profiles:
        click.echo("No profiles found.")
        return

    for profile in profiles:
        keys = ", ".join(sorted(profile.variables.keys()))
        click.echo(f"  {profile.name} [{profile.context}]  —  {keys}")


@cli.command("remove")
@click.argument("profile_name")
@click.pass_context
def remove_command(ctx: click.Context, profile_name: str) -> None:
    """Remove a profile by name."""
    store: ProfileStore = ctx.obj["store"]
    audit: AuditLog = ctx.obj["audit"]

    removed = store.remove_profile(profile_name)
    if not removed:
        raise click.ClickException(f"Profile '{profile_name}' not found.")

    audit.record("remove", profile_name)
    click.echo(f"Profile '{profile_name}' removed.")


@cli.command("resolve")
@click.argument("profile_names", nargs=-1, required=True)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["shell", "dotenv", "json"]),
    default="shell",
    show_default=True,
    help="Output format for resolved variables.",
)
@click.pass_context
def resolve_command(ctx: click.Context, profile_names: tuple, fmt: str) -> None:
    """Resolve and export variables from one or more profiles (chained)."""
    store: ProfileStore = ctx.obj["store"]
    audit: AuditLog = ctx.obj["audit"]

    resolver = ProfileResolver(store)
    try:
        variables = resolver.resolve(list(profile_names))
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    output = export_variables(variables, fmt)
    click.echo(output)

    audit.record("resolve", ",".join(profile_names), details={"format": fmt})


@cli.command("audit")
@click.option("--limit", default=20, show_default=True, help="Number of recent entries to show.")
@click.pass_context
def audit_command(ctx: click.Context, limit: int) -> None:
    """Show recent audit log entries."""
    audit: AuditLog = ctx.obj["audit"]
    entries = audit.entries()[-limit:]

    if not entries:
        click.echo("No audit entries found.")
        return

    for entry in entries:
        detail_str = f"  {entry.details}" if entry.details else ""
        click.echo(f"[{entry.timestamp}] {entry.action} — {entry.profile}{detail_str}")


def main() -> None:
    """Package entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
