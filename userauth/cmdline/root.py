import click

from .database import cmd_database
from .server import cmd_server


@click.group()
def cmd_root():
    """Root command for the CLI is empty."""


cmd_root.add_command(cmd_server)
cmd_root.add_command(cmd_database)
