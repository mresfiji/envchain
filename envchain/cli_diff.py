"""CLI command for diffing two profiles or snapshots."""

import click
from envchain.profile import ProfileStore
from envchain.snapshot import SnapshotStore
from envchain.differ import diff_variables, format_diff


@click.group()
def cli():
    """Diff environment variable profiles or snapshots."""


@cli.command("profiles")
@click.argument("profile_a")
@click.argument("profile_b")
@click.option("--store", "store_path", default="profiles.json", show_default=True)
@click.option("--show-values", is_flag=True, default=False, help="Reveal variable values")
def diff_profiles_command(profile_a: str, profile_b: str, store_path: str, show_values: bool):
    """Diff variables between two profiles."""
    store = ProfileStore(store_path)
    a = store.get(profile_a)
    b = store.get(profile_b)

    if a is None:
        raise click.ClickException(f"Profile '{profile_a}' not found.")
    if b is None:
        raise click.ClickException(f"Profile '{profile_b}' not found.")

    result = diff_variables(a.variables, b.variables)
    click.echo(f"Diff: {profile_a} → {profile_b}")
    click.echo(f"Summary: {result.summary()}")

    if result.has_changes:
        lines = format_diff(result, mask_values=not show_values)
        for line in lines:
            click.echo(line)
    else:
        click.echo("  (no differences)")


@cli.command("snapshots")
@click.argument("snapshot_a")
@click.argument("snapshot_b")
@click.option("--store", "store_path", default="snapshots.json", show_default=True)
@click.option("--show-values", is_flag=True, default=False, help="Reveal variable values")
def diff_snapshots_command(snapshot_a: str, snapshot_b: str, store_path: str, show_values: bool):
    """Diff resolved variables between two snapshots."""
    store = SnapshotStore(store_path)
    a = store.get(snapshot_a)
    b = store.get(snapshot_b)

    if a is None:
        raise click.ClickException(f"Snapshot '{snapshot_a}' not found.")
    if b is None:
        raise click.ClickException(f"Snapshot '{snapshot_b}' not found.")

    result = diff_variables(a.variables, b.variables)
    click.echo(f"Diff: {snapshot_a} → {snapshot_b}")
    click.echo(f"Summary: {result.summary()}")

    if result.has_changes:
        lines = format_diff(result, mask_values=not show_values)
        for line in lines:
            click.echo(line)
    else:
        click.echo("  (no differences)")
