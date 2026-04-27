"""CLI commands for linting environment variable profiles."""

import json
import click
from envchain.profile import ProfileStore
from envchain.linter import lint_profile


@click.group(name="lint")
def cli():
    """Lint profiles for common issues."""


@cli.command(name="run")
@click.argument("profile_names", nargs=-1, required=True)
@click.option("--store", "store_path", default="profiles.json", show_default=True,
              help="Path to the profile store file.")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]),
              default="text", show_default=True, help="Output format.")
@click.option("--strict", is_flag=True, default=False,
              help="Exit with non-zero code if any warnings are found.")
def lint_command(profile_names, store_path, output_format, strict):
    """Lint one or more profiles and report issues."""
    store = ProfileStore(store_path)
    all_results = []
    exit_code = 0

    for name in profile_names:
        profile = store.get(name)
        if profile is None:
            click.echo(f"Profile '{name}' not found.", err=True)
            exit_code = 2
            continue

        result = lint_profile(profile)
        all_results.append(result)

        if result.has_errors:
            exit_code = 1
        elif strict and result.has_warnings:
            exit_code = 1

    if output_format == "json":
        output = [
            {
                "profile": r.profile_name,
                "issues": [i.to_dict() for i in r.issues],
            }
            for r in all_results
        ]
        click.echo(json.dumps(output, indent=2))
    else:
        for result in all_results:
            if not result.issues:
                click.echo(f"[OK] {result.profile_name}: no issues found.")
                continue
            click.echo(f"[LINT] {result.summary()}")
            for issue in result.issues:
                prefix = "ERROR" if issue.level == "error" else "WARN "
                var_hint = f" [{issue.variable}]" if issue.variable else ""
                click.echo(f"  {prefix} {issue.code}{var_hint}: {issue.message}")

    raise SystemExit(exit_code)
