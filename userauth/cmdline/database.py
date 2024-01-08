import asyncio

import click


@click.group("database")
def cmd_database():
    """Commands to manipulate the database."""


@cmd_database.command("create")
def cmd_database_create():
    """Create and initialize the new database."""
    from userauth.database import safe_create_db

    asyncio.run(safe_create_db())


@cmd_database.command("adduser")
@click.option(
    "-u",
    "--username",
    type=str,
    prompt=True,
    required=True,
    default="username",
    show_default=True,
    help="User name.",
)
@click.option(
    "-p",
    "--password",
    type=str,
    prompt=True,
    required=True,
    default="password",
    show_default=True,
    help="User password.",
)
def cmd_database_adduser(username, password):
    """Add a new user to the database."""

    async def internal_adduser(username, password):
        from userauth.database import get_database_manager

        fake_email = f"{username}@fakemail.com"
        async for mydatabase in get_database_manager():
            output = await mydatabase.create_user(
                username,
                password,
                fake_email,
            )
        return output

    created = asyncio.run(internal_adduser(username, password))
    if created is not None:
        print(f"New user {username} created!")
    else:
        print(f"User {username} already exists.")


@cmd_database.command("makeadmin")
@click.option(
    "-u",
    "--username",
    type=str,
    prompt=True,
    required=True,
    default="username",
    show_default=True,
    help="User name.",
)
def cmd_database_makeadmin(username):
    from userauth.common.roles import Role

    async def internal_makeadmin(username):
        from userauth.database import get_database_manager

        async for mydatabase in get_database_manager():
            dbuser = await mydatabase.get_user(username=username)
            if dbuser is None:
                return None
            output = await mydatabase.update_user(
                uuid=dbuser.uuid,
                new_role=Role.admin,
                new_username=username,
            )
        return output

    updated = asyncio.run(internal_makeadmin(username))
    if updated is None:
        print(f"User {username} not found.")
    else:
        print(f"User {username} is now admin!")
