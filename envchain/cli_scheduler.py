"""CLI commands for managing scheduled exports."""

import click
from pathlib import Path
from envchain.scheduler import ScheduleStore, ScheduledExport, SchedulerError
from envchain.resolver import ProfileResolver
from envchain.profile import ProfileStore
from envchain.exporter import export_variables

DEFAULT_SCHEDULE_PATH = Path.home() / ".envchain" / "schedules.json"
DEFAULT_PROFILE_PATH = Path.home() / ".envchain" / "profiles.json"


@click.group()
def cli():
    """Manage scheduled environment exports."""


@cli.command("add")
@click.argument("label")
@click.option("--profiles", "-p", required=True, multiple=True, help="Profile names to chain.")
@click.option("--output", "-o", required=True, help="Output file path.")
@click.option("--format", "-f", "fmt", default="dotenv", show_default=True,
              type=click.Choice(["shell", "dotenv", "json"]), help="Export format.")
@click.option("--schedule-file", default=str(DEFAULT_SCHEDULE_PATH), hidden=True)
def add_command(label, profiles, output, fmt, schedule_file):
    """Register a new scheduled export."""
    store = ScheduleStore(Path(schedule_file))
    try:
        schedule = ScheduledExport(
            profile_names=list(profiles),
            output_path=output,
            format=fmt,
            label=label,
        )
        store.add(schedule)
        click.echo(f"Scheduled export '{label}' added.")
    except SchedulerError as e:
        raise click.ClickException(str(e))


@cli.command("remove")
@click.argument("label")
@click.option("--schedule-file", default=str(DEFAULT_SCHEDULE_PATH), hidden=True)
def remove_command(label, schedule_file):
    """Remove a scheduled export by label."""
    store = ScheduleStore(Path(schedule_file))
    try:
        store.remove(label)
        click.echo(f"Scheduled export '{label}' removed.")
    except SchedulerError as e:
        raise click.ClickException(str(e))


@cli.command("list")
@click.option("--schedule-file", default=str(DEFAULT_SCHEDULE_PATH), hidden=True)
def list_command(schedule_file):
    """List all scheduled exports."""
    store = ScheduleStore(Path(schedule_file))
    schedules = store.all()
    if not schedules:
        click.echo("No scheduled exports.")
        return
    for s in schedules:
        status = "active" if s.active else "inactive"
        profiles = ", ".join(s.profile_names)
        click.echo(f"[{status}] {s.label}: profiles=[{profiles}] -> {s.output_path} ({s.format})")


@cli.command("run")
@click.argument("label")
@click.option("--schedule-file", default=str(DEFAULT_SCHEDULE_PATH), hidden=True)
@click.option("--profile-file", default=str(DEFAULT_PROFILE_PATH), hidden=True)
def run_command(label, schedule_file, profile_file):
    """Manually trigger a scheduled export."""
    store = ScheduleStore(Path(schedule_file))
    schedule = store.get(label)
    if not schedule:
        raise click.ClickException(f"No schedule found with label '{label}'.")
    profile_store = ProfileStore(Path(profile_file))
    resolver = ProfileResolver(profile_store)
    variables = resolver.resolve(schedule.profile_names)
    output = export_variables(variables, schedule.format)
    Path(schedule.output_path).write_text(output)
    click.echo(f"Exported '{label}' to {schedule.output_path}.")
