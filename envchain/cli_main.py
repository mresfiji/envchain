"""Main CLI entry point for envchain, aggregating all sub-command groups."""

import click

from envchain.cli import cli as core_cli
from envchain.cli_resolve import cli as resolve_cli
from envchain.cli_snapshot import cli as snapshot_cli
from envchain.cli_diff import cli as diff_cli
from envchain.cli_tag import cli as tag_cli
from envchain.cli_template import cli as template_cli
from envchain.cli_scheduler import cli as scheduler_cli
from envchain.cli_history import cli as history_cli
from envchain.cli_lint import cli as lint_cli
from envchain.cli_pin import cli as pin_cli
from envchain.cli_rollback import cli as rollback_cli
from envchain.cli_compare import cli as compare_cli
from envchain.cli_watchdog import cli as watchdog_cli


@click.group()
@click.version_option(package_name="envchain")
def main():
    """envchain — Manage and chain environment variable profiles."""


main.add_command(core_cli, name="profile")
main.add_command(resolve_cli, name="resolve")
main.add_command(snapshot_cli, name="snapshot")
main.add_command(diff_cli, name="diff")
main.add_command(tag_cli, name="tag")
main.add_command(template_cli, name="template")
main.add_command(scheduler_cli, name="scheduler")
main.add_command(history_cli, name="history")
main.add_command(lint_cli, name="lint")
main.add_command(pin_cli, name="pin")
main.add_command(rollback_cli, name="rollback")
main.add_command(compare_cli, name="compare")
main.add_command(watchdog_cli, name="watchdog")


if __name__ == "__main__":
    main()
