"""CLI commands for rendering profile variables with template interpolation."""

import json
import os
import sys

import click

from envchain.profile import ProfileStore
from envchain.resolver import ProfileResolver
from envchain.templating import TemplateError, render_variables


DEFAULT_STORE = os.path.expanduser("~/.envchain/profiles.json")


@click.group("template")
def cli() -> None:
    """Render profile variables using template interpolation."""


@cli.command("render")
@click.argument("profiles", nargs=-1, required=True)
@click.option(
    "--store",
    default=DEFAULT_STORE,
    show_default=True,
    help="Path to the profile store file.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["shell", "json", "dotenv"], case_sensitive=False),
    default="shell",
    show_default=True,
    help="Output format for rendered variables.",
)
@click.option(
    "--env/--no-env",
    default=True,
    show_default=True,
    help="Include current process environment as interpolation context.",
)
def render_command(profiles: tuple, store: str, fmt: str, env: bool) -> None:
    """Resolve PROFILES (chained) and render template references.

    Variables may contain ${OTHER_VAR} or ${OTHER_VAR:default} references
    that are substituted from earlier variables or the current environment.
    """
    profile_store = ProfileStore(store)
    resolver = ProfileResolver(profile_store)

    try:
        merged = resolver.resolve(list(profiles))
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error resolving profiles: {exc}", err=True)
        sys.exit(1)

    context = dict(os.environ) if env else {}

    try:
        rendered = render_variables(merged, context=context)
    except TemplateError as exc:
        click.echo(f"Template error: {exc}", err=True)
        sys.exit(1)

    if fmt == "json":
        click.echo(json.dumps(rendered, indent=2, sort_keys=True))
    elif fmt == "dotenv":
        for key, value in sorted(rendered.items()):
            click.echo(f"{key}={value}")
    else:  # shell
        for key, value in sorted(rendered.items()):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            click.echo(f'export {key}="{escaped}"')
