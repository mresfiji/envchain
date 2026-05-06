"""CLI commands for scoring profiles."""
import json
import os

import click

from envchain.profile import ProfileStore
from envchain.scorer import score_profile


@click.group("score")
def cli():
    """Score profile quality."""


@cli.command("run")
@click.argument("profile_name")
@click.option("--store", "store_path", default=None, help="Path to profile store JSON.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
def score_command(profile_name: str, store_path: str | None, fmt: str):
    """Score a single profile and display the result."""
    path = store_path or os.environ.get("ENVCHAIN_STORE", "profiles.json")
    store = ProfileStore(path)
    profile = store.get(profile_name)
    if profile is None:
        raise click.ClickException(f"Profile '{profile_name}' not found.")

    result = score_profile(profile)

    if fmt == "json":
        click.echo(json.dumps({
            "profile": result.profile_name,
            "total": result.total,
            "max_total": result.max_total,
            "percentage": result.percentage,
            "grade": result.grade,
            "breakdown": [b.to_dict() for b in result.breakdown],
        }, indent=2))
    else:
        click.echo(result.summary())
        for b in result.breakdown:
            status = "✓" if b.points == b.max_points else "✗"
            click.echo(f"  {status} [{b.category}] {b.points}/{b.max_points} — {b.reason}")


@cli.command("all")
@click.option("--store", "store_path", default=None, help="Path to profile store JSON.")
@click.option("--min-grade", default=None, help="Only show profiles at or below this grade (A-F).")
def score_all_command(store_path: str | None, min_grade: str | None):
    """Score all profiles in the store."""
    path = store_path or os.environ.get("ENVCHAIN_STORE", "profiles.json")
    store = ProfileStore(path)
    profiles = store.list()

    if not profiles:
        click.echo("No profiles found.")
        return

    grade_order = ["A", "B", "C", "D", "F"]
    results = [score_profile(p) for p in profiles]
    results.sort(key=lambda r: (grade_order.index(r.grade), -r.total))

    for result in results:
        if min_grade and grade_order.index(result.grade) < grade_order.index(min_grade):
            continue
        click.echo(result.summary())
