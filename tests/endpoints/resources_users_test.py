from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from userauth.common.roles import Role
from userauth.database.models import UserEntry
from userauth.endpoints.resources import (
    delete_users_id,
    get_users,
    get_users_id,
    get_users_me,
    post_users_id_validate,
    update_users_id,
)

pytest_plugins = ("pytest_asyncio",)

admin_user = UserEntry(
    uuid=uuid4(),
    role=Role.admin,
    username="admin_user",
    email="admin_user@email.com",
    name="Barack",
    surname="Obama",
    hashed_password="password",
)

normal_user = UserEntry(
    uuid=uuid4(),
    role=Role.normal,
    username="normal_user",
    email="normal_user@email.com",
    name="Tom",
    surname="Cruise",
    hashed_password="password",
)

celebrity_user = UserEntry(
    uuid=uuid4(),
    role=Role.celebrity,
    username="celebrity_user",
    email="celebrity_user@email.com",
    name="Tom",
    surname="Cruise",
    hashed_password="password",
)


class MockedManager:
    def __init__(self):
        self.admin_user_updated = False
        self.admin_user_deleted = False
        self.celebrity_user_deleted = False
        self.celebrity_user_deleted = False
        self.normal_user_updated = False
        self.normal_user_deleted = False

    async def get_users(self):
        return [admin_user, normal_user, celebrity_user]

    async def get_user(self, uuid=None, username=None):
        if username == admin_user.username or uuid == admin_user.uuid:
            return admin_user

        if username == celebrity_user.username or uuid == celebrity_user.uuid:
            return celebrity_user

        if username == normal_user.username or uuid == normal_user.uuid:
            return normal_user

    async def update_user(self, uuid, *args, **kwargs):
        if uuid == admin_user.uuid:
            self.admin_user_updated = True
            return admin_user

        if uuid == celebrity_user.uuid:
            self.celebrity_user_updated = True
            return celebrity_user

        if uuid == normal_user.uuid:
            self.normal_user_updated = True
            return normal_user

    async def delete_user(self, uuid):
        if uuid == admin_user.uuid:
            self.admin_user_deleted = True

        if uuid == celebrity_user.uuid:
            self.celebrity_user_deleted = True

        if uuid == normal_user.uuid:
            self.normal_user_deleted = True


@pytest.mark.asyncio
async def test_get_users_me():
    """Test that you get yourself."""
    result = await get_users_me(active_user=normal_user)
    assert result.username == "normal_user"


@pytest.mark.asyncio
async def test_get_users_id():
    """Test that you can only get yourself except admins."""
    mocked_manager = MockedManager()

    result = await get_users_id(
        user_id=normal_user.uuid,
        active_user=normal_user,
        dbmanager=mocked_manager,
    )
    assert result.username == "normal_user"

    result = await get_users_id(
        user_id=normal_user.uuid,
        active_user=admin_user,
        dbmanager=mocked_manager,
    )
    assert result.username == "normal_user"

    result = await get_users_id(
        user_id=celebrity_user.uuid,
        active_user=admin_user,
        dbmanager=mocked_manager,
    )
    assert result.username == "celebrity_user"

    with pytest.raises(HTTPException) as excinfo:
        result = await get_users_id(
            user_id=celebrity_user.uuid,
            active_user=normal_user,
            dbmanager=mocked_manager,
        )
    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND

    with pytest.raises(HTTPException) as excinfo:
        result = await get_users_id(
            user_id=normal_user.uuid,
            active_user=celebrity_user,
            dbmanager=mocked_manager,
        )
    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_users():
    """Test that only admins can see all users."""
    mocked_manager = MockedManager()

    result = await get_users(active_user=admin_user, dbmanager=mocked_manager)
    assert len(result) == 3

    with pytest.raises(HTTPException) as excinfo:
        result = await get_users(
            active_user=normal_user,
            dbmanager=mocked_manager,
        )
    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_users_id():
    """Test that you can only update your username and admins also role."""

    updated_user = UserEntry(
        uuid=normal_user.uuid,
        role=Role.normal,
        username="normal_user",
        email="normal_user@email.com",
        name="Tom",
        surname="Cruise",
        hashed_password="password",
    )

    request_arguments = {
        "user_id": normal_user.uuid,
        "updated_user": updated_user,
        "active_user": None,
        "dbmanager": None,
    }

    # UPDATING USERNAME
    request_arguments["updated_user"].username = "changed_username"

    request_arguments["active_user"] = normal_user
    request_arguments["dbmanager"] = MockedManager()
    result = await update_users_id(**request_arguments)
    assert result.username == "normal_user"
    assert request_arguments["dbmanager"].normal_user_updated

    request_arguments["active_user"] = admin_user
    request_arguments["dbmanager"] = MockedManager()
    result = await update_users_id(**request_arguments)
    assert result.username == "normal_user"
    assert request_arguments["dbmanager"].normal_user_updated

    # UPDATING ROLE
    request_arguments["updated_user"].role = Role.celebrity

    request_arguments["active_user"] = normal_user
    request_arguments["dbmanager"] = MockedManager()
    with pytest.raises(HTTPException) as excinfo:
        result = await update_users_id(**request_arguments)
    assert excinfo.value.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    request_arguments["active_user"] = admin_user
    request_arguments["dbmanager"] = MockedManager()
    result = await update_users_id(**request_arguments)
    assert result.username == "normal_user"
    assert request_arguments["dbmanager"].normal_user_updated

    # UPDATING ANYTHING ELSE
    request_arguments["updated_user"].name = "namechange"

    request_arguments["dbmanager"] = MockedManager()
    with pytest.raises(HTTPException) as excinfo:
        result = await update_users_id(**request_arguments)
    assert excinfo.value.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.asyncio
async def test_delete_users_id():
    """Test that you can only delete yourself."""

    request_arguments = {
        "user_id": normal_user.uuid,
        "active_user": normal_user,
        "dbmanager": None,
    }

    request_arguments["dbmanager"] = MockedManager()
    result = await delete_users_id(**request_arguments)
    assert result is None
    assert request_arguments["dbmanager"].normal_user_deleted

    request_arguments["active_user"] = admin_user
    request_arguments["dbmanager"] = MockedManager()
    with pytest.raises(HTTPException) as excinfo:
        result = await delete_users_id(**request_arguments)
    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.skip(reason="This test takes a bit too long...")
@pytest.mark.asyncio
async def test_post_users_id_validate():
    """Test celebrity recognition."""
    from pathlib import Path

    root_path = Path(__file__).parent.parent.parent
    file_path = root_path / "userauth" / "picmodel" / "tom.jpeg"

    with open(file_path, "rb") as image_file:
        filedata = image_file.read()

    request_arguments = {
        "file": filedata,
        "active_user": normal_user,
        "dbmanager": None,
    }

    request_arguments["active_user"] = normal_user
    request_arguments["dbmanager"] = MockedManager()
    result = await post_users_id_validate(**request_arguments)
    assert result.username == "normal_user"
    assert request_arguments["dbmanager"].normal_user_updated

    request_arguments["active_user"] = admin_user
    request_arguments["dbmanager"] = MockedManager()
    with pytest.raises(HTTPException) as excinfo:
        await post_users_id_validate(**request_arguments)
    assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
