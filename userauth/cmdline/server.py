import click


@click.group("server")
def cmd_server():
    """Commands to manipulate the server."""


@cmd_server.command("start")
@click.option(
    "--ip",
    type=str,
    default="0.0.0.0",
    help="IP to use for deploying the server.",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port to use for deploying the server.",
)
def cmd_server_start(ip, port):
    """Start the REST API server."""
    from contextlib import asynccontextmanager

    import uvicorn
    from fastapi import FastAPI

    from userauth.database import safe_create_db
    from userauth.endpoints import authentication, resources

    @asynccontextmanager
    async def lifespan_function(app: FastAPI):
        """Create the database and return control to API service.

        There is nothing after yielding because there are no resources
        to release at shutdown time.
        """
        await safe_create_db()
        yield

    app = FastAPI(
        title="UserAuth",
        description="A python-based user authentication REST-API server for automated celebrity recognition.",
        version="0.1.0",
        lifespan=lifespan_function,
    )
    app.include_router(router=authentication)
    app.include_router(router=resources)

    uvicorn.run(app=app, host=ip, port=port)
