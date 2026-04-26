"""Unified entry point that groups all envchain CLI sub-commands."""

import click
from envchain.cli import cli as profile_cli
from envchain.cli_resolve import cli as resolve_cli
from envchain.cli_snapshot import cli as snapshot_cli
from envchain.cli_diff import cli as diff_cli
from envchain.cli_tag import cli as tag_cli
from envchain.cli_template import cli as template_cli
from envchain.cli_scheduler import cli as scheduler_cli


@click.group()
@click.version_option(package_name="envchain")
def main():
    """envchain — manage and chain environment variable profiles."""


main.add_command(profile_cli, name="profile")
main.add_command(resolve_cli, name="resolve")
main.add_command(snapshot_cli, name="snapshot")
main.add_command(diff_cli, name="diff")
main.add_command(tag_cli, name="tag")
main.add_command(template_cli, name="template")
main.add_command(scheduler_cli, name="scheduler")


if __name__ == "__main__":
    main()
