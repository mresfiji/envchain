"""Main CLI entry point that registers all sub-command groups."""

from __future__ import annotations

import click

from envchain.cli import cli as profile_cli
from envchain.cli_resolve import cli as resolve_cli
from envchain.cli_snapshot import cli as snapshot_cli
from envchain.cli_diff import cli as diff_cli
from envchain.cli_tag import cli as tag_cli
from envchain.cli_template import cli as template_cli
from envchain.cli_scheduler import cli as scheduler_cli
from envchain.cli_history import cli as history_cli
from envchain.cli_lint import cli as lint_cli
from envchain.cli_pin import cli as pin_cli


@click.group()
def main():
    """envchain — manage and chain environment variable profiles."""


main.add_command(profile_cli, name="profile")
main.add_command(resolve_cli, name="resolve")
main.add_command(snapshot_cli, name="snapshot")
main.add_command(diff_cli, name="diff")
main.add_command(tag_cli, name="tag")
main.add_command(template_cli, name="template")
main.add_command(scheduler_cli, name="schedule")
main.add_command(history_cli, name="history")
main.add_command(lint_cli, name="lint")
main.add_command(pin_cli, name="pin")


if __name__ == "__main__":
    main()
