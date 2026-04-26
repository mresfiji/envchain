"""CLI commands for managing profile tags."""
import json
from pathlib import Path

import click

from envchain.tagging import TagError, TagIndex

DEFAULT_TAG_FILE = Path(".envchain_tags.json")


def _load_index(path: Path) -> TagIndex:
    if path.exists():
        data = json.loads(path.read_text())
        return TagIndex.from_dict(data)
    return TagIndex()


def _save_index(index: TagIndex, path: Path) -> None:
    path.write_text(json.dumps(index.to_dict(), indent=2))


@click.group()
@click.option("--tag-file", default=str(DEFAULT_TAG_FILE), show_default=True, help="Tag index file path.")
@click.pass_context
def cli(ctx: click.Context, tag_file: str) -> None:
    """Manage tags for envchain profiles."""
    ctx.ensure_object(dict)
    ctx.obj["tag_file"] = Path(tag_file)


@cli.command("add")
@click.argument("tag")
@click.argument("profile")
@click.pass_context
def add_command(ctx: click.Context, tag: str, profile: str) -> None:
    """Add TAG to PROFILE."""
    path: Path = ctx.obj["tag_file"]
    index = _load_index(path)
    try:
        index.add(tag, profile)
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc
    _save_index(index, path)
    click.echo(f"Tagged '{profile}' with '{tag}'.")


@cli.command("remove")
@click.argument("tag")
@click.argument("profile")
@click.pass_context
def remove_command(ctx: click.Context, tag: str, profile: str) -> None:
    """Remove TAG from PROFILE."""
    path: Path = ctx.obj["tag_file"]
    index = _load_index(path)
    try:
        index.remove(tag, profile)
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc
    _save_index(index, path)
    click.echo(f"Removed tag '{tag}' from '{profile}'.")


@cli.command("list")
@click.option("--profile", default=None, help="Filter tags by profile name.")
@click.option("--tag", default=None, help="List profiles for a specific tag.")
@click.pass_context
def list_command(ctx: click.Context, profile: str | None, tag: str | None) -> None:
    """List tags or tagged profiles."""
    path: Path = ctx.obj["tag_file"]
    index = _load_index(path)
    if tag:
        profiles = index.profiles_for_tag(tag)
        if not profiles:
            click.echo(f"No profiles tagged with '{tag}'.")
        else:
            click.echo("\n".join(profiles))
    elif profile:
        tags = index.tags_for_profile(profile)
        if not tags:
            click.echo(f"No tags for profile '{profile}'.")
        else:
            click.echo("\n".join(tags))
    else:
        all_tags = index.all_tags()
        if not all_tags:
            click.echo("No tags defined.")
        else:
            click.echo("\n".join(all_tags))
