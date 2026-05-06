"""CLI commands for managing variable expiration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import click

from envchain.expirator import ExpirationError, ExpiryEntry, ExpiryStore

_DEFAULT_STORE = Path.home() / ".envchain" / "expiry.json"


def _get_store(env_path: str | None) -> ExpiryStore:
    path = Path(env_path) if env_path else _DEFAULT_STORE
    path.parent.mkdir(parents=True, exist_ok=True)
    return ExpiryStore(path)


@click.group("expiry")
def cli() -> None:
    """Manage variable expiration dates."""


@cli.command("set")
@click.argument("profile")
@click.argument("variable")
@click.argument("expires_at")
@click.option("--note", default="", help="Optional note about this expiry.")
@click.option("--store", "env_store", envvar="ENVCHAIN_EXPIRY_STORE", default=None, hidden=True)
def set_command(profile: str, variable: str, expires_at: str, note: str, env_store: str | None) -> None:
    """Set an expiration date (ISO 8601) for a variable in a profile."""
    try:
        dt = datetime.fromisoformat(expires_at)
    except ValueError:
        raise click.ClickException(f"Invalid date format: {expires_at!r}. Use ISO 8601.")
    store = _get_store(env_store)
    entry = ExpiryEntry(profile=profile, variable=variable, expires_at=dt, note=note)
    store.set(entry)
    click.echo(f"Expiry set for {profile}::{variable} → {dt.isoformat()}")


@cli.command("unset")
@click.argument("profile")
@click.argument("variable")
@click.option("--store", "env_store", envvar="ENVCHAIN_EXPIRY_STORE", default=None, hidden=True)
def unset_command(profile: str, variable: str, env_store: str | None) -> None:
    """Remove an expiration entry."""
    store = _get_store(env_store)
    try:
        store.remove(profile, variable)
        click.echo(f"Expiry removed for {profile}::{variable}")
    except ExpirationError as exc:
        raise click.ClickException(str(exc))


@cli.command("list")
@click.option("--expired-only", is_flag=True, default=False, help="Show only expired entries.")
@click.option("--store", "env_store", envvar="ENVCHAIN_EXPIRY_STORE", default=None, hidden=True)
def list_command(expired_only: bool, env_store: str | None) -> None:
    """List all expiration entries."""
    store = _get_store(env_store)
    entries = store.expired_entries() if expired_only else store.all_entries()
    if not entries:
        click.echo("No expiry entries found.")
        return
    now = datetime.now(timezone.utc)
    for e in sorted(entries, key=lambda x: x.expires_at):
        status = "EXPIRED" if e.is_expired(now) else "ok"
        note_str = f"  # {e.note}" if e.note else ""
        click.echo(f"[{status}] {e.profile}::{e.variable}  expires={e.expires_at.isoformat()}{note_str}")


@cli.command("check")
@click.option("--fail-on-expired", is_flag=True, default=False)
@click.option("--store", "env_store", envvar="ENVCHAIN_EXPIRY_STORE", default=None, hidden=True)
def check_command(fail_on_expired: bool, env_store: str | None) -> None:
    """Report expired variables; optionally exit with code 1."""
    store = _get_store(env_store)
    expired = store.expired_entries()
    if not expired:
        click.echo("No expired variables.")
        return
    for e in expired:
        click.echo(f"EXPIRED: {e.profile}::{e.variable} (since {e.expires_at.isoformat()})")
    if fail_on_expired:
        raise SystemExit(1)
