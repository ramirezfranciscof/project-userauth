import os
from typing import Optional

from pydantic import BaseModel


class DatabaseEngineArguments(BaseModel):
    """Subclass holding the connect_args for creating the db engine."""

    check_same_thread: bool = False


class ServerConfig(BaseModel):
    """Class holding the server configuration."""

    # DATABASE_ENGINE_URL: str = "sqlite:///./sqlite3.db"
    DATABASE_ENGINE_URL: str = "sqlite+aiosqlite:///./sqlite3.db"
    DATABASE_ENGINE_ARGS: Optional[DatabaseEngineArguments] = DatabaseEngineArguments()

    # to get a string like this run:
    # openssl rand -hex 32
    AUTH_SECRET_KEY: str = (
        "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    )
    AUTH_ALGORITHM: str = "HS256"
    AUTH_EXPIRATION_MINS: int = 30


def envload_dburl():
    """Load the database URL from the environment."""

    username = os.getenv("POSTGRES_USERNAME")
    if username is None:
        raise RuntimeError("variable POSTGRES_USERNAME not set")

    password = os.getenv("POSTGRES_PASSWORD")
    if password is None:
        raise RuntimeError("variable POSTGRES_PASSWORD not set")

    hostname = os.getenv("POSTGRES_HOST")
    if hostname is None:
        raise RuntimeError("variable POSTGRES_HOST not set")

    hostport = os.getenv("POSTGRES_PORT")
    if hostport is None:
        raise RuntimeError("variable POSTGRES_PORT not set")

    dbname = os.getenv("POSTGRES_DBNAME")
    if dbname is None:
        raise RuntimeError("variable POSTGRES_DBNAME not set")

    postgresql_string = f"postgresql+asyncpg://{str(username)}:{str(password)}"
    postgresql_string += f"@{str(hostname)}:{str(hostport)}/{str(dbname)}"

    return postgresql_string


deployment_type = os.getenv("DEPLOYMENT_TYPE", default="DEV")

if deployment_type == "PROD":
    dburl = envload_dburl()
    SERVER_CONFIG = ServerConfig(
        DATABASE_ENGINE_URL=dburl,
        DATABASE_ENGINE_ARGS=None,
    )
else:
    SERVER_CONFIG = ServerConfig()
