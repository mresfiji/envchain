"""CLI commands for summarizing profiles and the profile store."""

import click

from envchain.profile import ProfileStore
from envchain.summarizer import summarize_profile, summarize_store


@click.group("summarize")
def cli():
    """Summarize profiles or the entire store."""


@cli.command("profile")
@click.argument("name")
@click.option("--store", "store_path", default="profiles.json", show_default=True,
              help="Path to the profile store.")
@click.option("--detail", is_flag=True, default=False,
              help="Show detailed summary including variable names.")
@click.option("--note", default=None, help="Optional note to attach to the summary.")
def profile_command(name: str, store_path: str, detail: bool, note):
    """Summarize a single profile by NAME."""
    store = ProfileStore(store_path)
    profile = store.get_profile(name)
    if profile is None:
        raise click.ClickException(f"Profile '{name}' not found.")
    summary = summarize_profile(profile, note=note)
    if detail:
        click.echo(summary.detail())
    else:
        click.echo(summary.short())


@cli.command("store")
@click.option("--store", "store_path", default="profiles.json", show_default=True,
              help="Path to the profile store.")
@click.option("--detail", is_flag=True, default=False,
              help="Show per-profile details.")
def store_command(store_path: str, detail: bool):
    """Summarize all profiles in the store."""
    store = ProfileStore(store_path)
    result = summarize_store(store)
    click.echo(result.short())
    if detail and result.profiles:
        click.echo("")
        for ps in result.profiles:
            click.echo(ps.detail())
            click.echo("")
