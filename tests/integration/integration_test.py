"""
Test the deployed app with a mock database.
"""
import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from userauth.database.manager import DatabaseManager
from userauth.database.models import Base
from userauth.database.session import get_database_manager
from userauth.endpoints import authentication, resources

################################################################################
# SETUP DB IN MEMORY
################################################################################

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite://"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


asyncio.run(create_db())


################################################################################
# SETUP REST-API WITH DB MOCK
################################################################################


async def get_test_manager():
    test_session = AsyncSession(engine, autocommit=False, autoflush=False)
    try:
        yield DatabaseManager(test_session)
    finally:
        await test_session.close()


app = FastAPI(
    title="UserAuth",
    description="A python-based user authentication REST-API server for automated celebrity recognition.",
    version="0.1.0",
)
app.include_router(router=authentication)
app.include_router(router=resources)

app.dependency_overrides[get_database_manager] = get_test_manager

test_client = TestClient(app)


################################################################################
# RUN INTEGRATION TESTS
################################################################################


def test_user_registration():
    """Test that unregistered users can register."""

    common_headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    user_params = {"name": "name", "surname": "surname"}

    user_data = {"password": "password"}

    # CREATE FIRST USER
    user_params["username"] = "first_username"
    user_data["email"] = "first@email.com"
    response = test_client.post(
        "/users",
        headers=common_headers,
        params=user_params,
        data=user_data,
    )
    assert response.status_code == 201

    # VERIFY EMAIL UNIQUENESS
    user_params["username"] = "second_username"
    user_data["email"] = "first@email.com"
    response = test_client.post(
        "/users",
        headers=common_headers,
        params=user_params,
        data=user_data,
    )
    assert response.status_code == 409

    # VERIFY USERNAME UNIQUENESS
    user_params["username"] = "first_username"
    user_data["email"] = "second@email.com"
    response = test_client.post(
        "/users",
        headers=common_headers,
        params=user_params,
        data=user_data,
    )
    assert response.status_code == 409

    # ALL IS GOOD
    user_params["username"] = "second_username"
    user_data["email"] = "second@email.com"
    response = test_client.post(
        "/users",
        headers=common_headers,
        params=user_params,
        data=user_data,
    )
    assert response.status_code == 201


################################################################################


def test_user_access():
    """Test access rights of registered users."""

    common_headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    user_params = {"name": "name", "surname": "surname"}

    user_data = {"password": "password"}

    # REGISTER 2 USERS
    user_params["username"] = "username01"
    user_data["email"] = "username01@email.com"
    response = test_client.post(
        "/users",
        headers=common_headers,
        params=user_params,
        data=user_data,
    )
    assert response.status_code == 201
    user01_uuid = response.json()["uuid"]

    user_params["username"] = "username02"
    user_data["email"] = "username02@email.com"
    response = test_client.post(
        "/users",
        headers=common_headers,
        params=user_params,
        data=user_data,
    )
    assert response.status_code == 201
    user02_uuid = response.json()["uuid"]

    # USER 1 LOGS IN
    response = test_client.post(
        "/token",
        headers=common_headers,
        data={"username": "username01", "password": "password"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    user01_header = {"accept": "application/json", "Authorization": f"Bearer {token}"}

    # USER 2 LOGS IN
    response = test_client.post(
        "/token",
        headers=common_headers,
        data={"username": "username02", "password": "password"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    user02_header = {"accept": "application/json", "Authorization": f"Bearer {token}"}

    # USER 1 CAN SEE ITS DATA BUT NOT FROM USER 2
    response = test_client.get(f"/users/me", headers=user01_header)
    assert response.status_code == 200

    response = test_client.get(f"/users/{user01_uuid}", headers=user01_header)
    assert response.status_code == 200

    response = test_client.get(f"/users/{user02_uuid}", headers=user01_header)
    assert response.status_code == 404

    # USER 2 CAN SEE ITS DATA BUT NOT FROM USER 1
    response = test_client.get(f"/users/me", headers=user02_header)
    assert response.status_code == 200

    response = test_client.get(f"/users/{user01_uuid}", headers=user02_header)
    assert response.status_code == 404

    response = test_client.get(f"/users/{user02_uuid}", headers=user02_header)
    assert response.status_code == 200

    # USER LOGINS AGAIN
    response = test_client.post(
        "/token",
        headers=common_headers,
        data={"username": "username01", "password": "password"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    user01_header = {"accept": "application/json", "Authorization": f"Bearer {token}"}

    # USER 1 SHOULD SEE 2 LOGINS, USER 2 SHOULD SEE 1
    response = test_client.get(f"/users/{user01_uuid}/logins", headers=user01_header)
    assert response.status_code == 200
    assert len(list(response.json())) == 2

    response = test_client.get(f"/users/{user02_uuid}/logins", headers=user02_header)
    assert response.status_code == 200
    assert len(list(response.json())) == 1

    # USER 1 CAN ONLY DELETE ITSELF
    # (After which credentials no longer work)
    response = test_client.delete(f"/users/{user02_uuid}", headers=user01_header)
    assert response.status_code == 404

    response = test_client.get(f"/users/me", headers=user01_header)
    assert response.status_code == 200

    response = test_client.delete(f"/users/{user01_uuid}", headers=user01_header)
    assert response.status_code == 204

    response = test_client.get(f"/users/me", headers=user01_header)
    assert response.status_code == 401

    response = test_client.delete(f"/users/{user02_uuid}", headers=user02_header)
    assert response.status_code == 204
