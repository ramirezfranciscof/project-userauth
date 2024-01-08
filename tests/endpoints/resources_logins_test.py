from datetime import datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from userauth.common.roles import Role
from userauth.database.models import LoginEntry, UserEntry
from userauth.endpoints.resources import (
    get_logins,
    get_logins_id,
    get_users_id_logins,
    get_users_id_logins_id,
    get_users_me_logins,
    get_users_me_logins_id,
)

pytest_plugins = ("pytest_asyncio",)

admin_user = UserEntry(
    uuid=uuid4(),
    role=Role.admin,
    username="admin_user",
    email="admin_user@email.com",
    name="name",
    surname="surname",
    hashed_password="password",
)

normal_user = UserEntry(
    uuid=uuid4(),
    role=Role.normal,
    username="normal_user",
    email="normal_user@email.com",
    name="name",
    surname="surname",
    hashed_password="password",
)

normal_login = LoginEntry(
    uuid=uuid4(),
    user=normal_user.uuid,
    ctime=datetime.now(),
)

admin_login = LoginEntry(
    uuid=uuid4(),
    user=admin_user.uuid,
    ctime=datetime.now(),
)


class MockedManager:
    async def get_logins(self, user_uuid):
        if user_uuid == admin_user.uuid:
            return [admin_login]

        if user_uuid == normal_user.uuid:
            return [normal_login]

        return [normal_login, admin_login]

    async def get_login(self, uuid):
        if uuid == admin_login.uuid:
            return admin_login

        if uuid == normal_login.uuid:
            return normal_login

    async def get_user(self, uuid=None, username=None):
        if username == admin_user.username or uuid == admin_user.uuid:
            return admin_user

        if username == normal_user.username or uuid == normal_user.uuid:
            return normal_user


@pytest.mark.asyncio
async def test_get_users_me_logins():
    """Test that you get logins through /me."""

    request_arguments = {
        "active_user": normal_user,
        "dbmanager": MockedManager(),
    }
    result = await get_users_me_logins(**request_arguments)
    assert [res.uuid for res in result] == [normal_login.uuid]

    request_arguments["login_id"] = normal_login.uuid
    result = await get_users_me_logins_id(**request_arguments)
    assert result.uuid == normal_login.uuid


@pytest.mark.asyncio
async def test_get_users_id_logins():
    """Test that you get logins through /users."""

    request_arguments = {
        "user_id": normal_user.uuid,
        "active_user": normal_user,
        "dbmanager": MockedManager(),
    }
    result = await get_users_id_logins(**request_arguments)
    assert [res.uuid for res in result] == [normal_login.uuid]

    request_arguments["login_id"] = normal_login.uuid
    result = await get_users_id_logins_id(**request_arguments)
    assert result.uuid == normal_login.uuid


@pytest.mark.asyncio
async def test_get_logins():
    """Test that only admins can get all logins."""

    request_arguments = {
        "active_user": admin_user,
        "dbmanager": MockedManager(),
    }
    result = await get_logins(**request_arguments)
    result = [res.uuid for res in result]
    result = set(result)
    assert result == {normal_login.uuid, admin_login.uuid}

    request_arguments = {
        "active_user": normal_user,
        "dbmanager": MockedManager(),
    }
    with pytest.raises(HTTPException) as excinfo:
        result = await get_logins(**request_arguments)
    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_logins_id():
    """Test that you can only see your logins, but admins can see any."""

    request_arguments = {
        "active_user": normal_user,
        "dbmanager": MockedManager(),
    }

    request_arguments["login_id"] = normal_login.uuid
    result = await get_logins_id(**request_arguments)
    assert result.uuid == normal_login.uuid

    request_arguments["login_id"] = admin_login.uuid
    with pytest.raises(HTTPException) as excinfo:
        result = await get_logins_id(**request_arguments)
    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND

    request_arguments = {
        "active_user": admin_user,
        "dbmanager": MockedManager(),
    }
    request_arguments["login_id"] = normal_login.uuid
    result = await get_logins_id(**request_arguments)
    assert result.uuid == normal_login.uuid
