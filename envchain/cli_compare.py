"""CLI commands for comparing profiles."""

import json
import click

from envchain.profile import ProfileStore
from envchain.comparator import compare_profiles, format_compare


@click.group()
def cli():
    """Compare environment variable profiles."""


@cli.command("profiles")
@click.argument("left")
@click.argument("right")
@click.option("--store", default="envchain_store.json", show_default=True, help="Profile store path.")
@click.option("--show-values", is_flag=True, default=False, help="Show actual values instead of masking.")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text", show_default=True)
def compare_profiles_command(left, right, store, show_values, output_format):
    """Compare two profiles by name."""
    ps = ProfileStore(store)
    left_profile = ps.get(left)
    right_profile = ps.get(right)

    if left_profile is None:
        raise click.ClickException(f"Profile '{left}' not found.")
    if right_profile is None:
        raise click.ClickException(f"Profile '{right}' not found.")

    result = compare_profiles(left_profile, right_profile)

    if output_format == "json":
        data = {
            "left": left,
            "right": right,
            "only_in_left": result.only_in_left if show_values else {k: "***" for k in result.only_in_left},
            "only_in_right": result.only_in_right if show_values else {k: "***" for k in result.only_in_right},
            "changed": (
                {k: {"left": lv, "right": rv} for k, (lv, rv) in result.changed.items()}
                if show_values
                else {k: {"left": "***", "right": "***"} for k in result.changed}
            ),
            "unchanged_count": len(result.unchanged),
            "has_differences": result.has_differences(),
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Comparing '{left}' <-> '{right}'")
        click.echo(f"Summary: {result.summary()}")
        lines = format_compare(result, mask_values=not show_values)
        if lines:
            click.echo("\n".join(lines))
        else:
            click.echo("(no differences)")


if __name__ == "__main__":
    cli()
