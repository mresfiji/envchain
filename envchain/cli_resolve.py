"""CLI commands for resolving and exporting profile chains."""

import click
from envchain.profile import ProfileStore
from envchain.resolver import ProfileResolver, ChainResolutionError
from envchain.exporter import export_variables, ExportFormatError, SUPPORTED_FORMATS

DEFAULT_STORE_PATH = "~/.envchain/profiles.json"


@click.group()
def cli():
    """envchain — manage and chain environment variable profiles."""
    pass


@cli.command("resolve")
@click.argument("profiles", nargs=-1, required=True)
@click.option(
    "--context", "-c",
    default="local",
    show_default=True,
    help="Context to resolve profiles in (local, staging, production).",
)
@click.option(
    "--format", "-f", "fmt",
    default="shell",
    show_default=True,
    type=click.Choice(list(SUPPORTED_FORMATS), case_sensitive=False),
    help="Output format for resolved variables.",
)
@click.option(
    "--store",
    default=DEFAULT_STORE_PATH,
    show_default=True,
    envvar="ENVCHAIN_STORE",
    help="Path to the profile store file.",
)
def resolve_command(profiles, context, fmt, store):
    """Resolve and export chained environment variable profiles.

    PROFILES is one or more profile names to chain in order.
    Later profiles override earlier ones for duplicate keys.

    Example:

        envchain resolve base db --context staging --format dotenv
    """
    try:
        profile_store = ProfileStore(store)
        resolver = ProfileResolver(profile_store)
        variables = resolver.resolve(list(profiles), context=context)
        output = export_variables(variables, fmt=fmt)
        if output:
            click.echo(output)
    except ChainResolutionError as exc:
        raise click.ClickException(str(exc))
    except ExportFormatError as exc:
        raise click.ClickException(str(exc))


if __name__ == "__main__":
    cli()
