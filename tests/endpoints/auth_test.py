from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from userauth.common.roles import Role
from userauth.database.models import UserEntry
from userauth.endpoints.auth import (
    create_access_token,
    get_current_active_user,
    login_for_access_token,
    post_users,
)

pytest_plugins = ("pytest_asyncio",)


def test_create_access_token():
    """Test the create_access_token method."""
    from jose import jwt

    from userauth.common.config import SERVER_CONFIG

    data = {"sub": "username"}
    access_token = create_access_token(data=data)
    broken_token = access_token.split(".")
    assert len(broken_token) == 3

    decoded_data = jwt.decode(
        token=access_token,
        key=SERVER_CONFIG.AUTH_SECRET_KEY,
        algorithms=SERVER_CONFIG.AUTH_ALGORITHM,
    )

    assert decoded_data["sub"] == "username"


@pytest.mark.asyncio
async def test_post_users():
    """Test the user creation endpoint."""

    class MockedManager:
        def __init__(self):
            self.user_created = False

        async def get_user(self, **kwargs):
            return None

        async def create_user(self, *args, **kwargs):
            self.user_created = True
            return UserEntry(
                uuid=uuid4(),
                role=Role.normal,
                username="username",
                email="email",
                name="name",
                surname="surname",
                hashed_password="password",
            )

    mocked_manager = MockedManager()

    result = await post_users(
        username="username",
        password="password",
        email="username@email.com",
        name="name",
        surname="surname",
        dbmanager=mocked_manager,
    )
    assert result.username == "username"
    assert mocked_manager.user_created


@pytest.mark.asyncio
async def test_post_users_existing():
    """Test the user existing."""

    class MockedManager:
        def __init__(self):
            self.user_created = False
            self.reference_user = UserEntry(
                uuid=uuid4(),
                role=Role.normal,
                username="username",
                email="email",
                name="name",
                surname="surname",
                hashed_password="password",
            )

        async def get_user(self, **kwargs):
            return self.reference_user

        async def create_user(self, *args, **kwargs):
            self.user_created = True
            return self.reference_user

    mocked_manager = MockedManager()

    with pytest.raises(HTTPException) as excinfo:
        await post_users(
            username="username",
            password="password",
            email="username@email.com",
            name="name",
            surname="surname",
            dbmanager=mocked_manager,
        )
    assert excinfo.value.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_login_for_access_token():
    """Test the login method."""
    from fastapi.security import OAuth2PasswordRequestForm

    class MockedManager:
        def __init__(self):
            self.login_recorded = False
            self.reference_user = UserEntry(
                uuid=uuid4(),
                role=Role.normal,
                username="username",
                email="email",
                name="name",
                surname="surname",
                hashed_password="password",
            )

        async def record_login(self, *args, **kwargs):
            self.login_recorded = True

        async def authenticate_user(self, *args, **kwargs):
            return self.reference_user

    mocked_manager = MockedManager()
    oauth_form = OAuth2PasswordRequestForm(username="username", password="password")
    result = await login_for_access_token(db=mocked_manager, form_data=oauth_form)
    assert "access_token" in result
    assert mocked_manager.login_recorded


@pytest.mark.asyncio
async def test_get_current_active_user():
    """Test the method to authenticate the active user."""
    from jose import jwt

    from userauth.common.config import SERVER_CONFIG

    class MockedManager:
        def __init__(self):
            self.good_user = False
            self.bad_user = False
            self.reference_user = UserEntry(
                uuid=uuid4(),
                role=Role.normal,
                username="encoded_username",
                email="email",
                name="name",
                surname="surname",
                hashed_password="password",
            )

        async def get_user(self, username):
            if username == "encoded_username":
                self.good_user = True
                return self.reference_user
            else:
                self.bad_user = True
                return None

    mocked_manager = MockedManager()
    new_token = jwt.encode(
        {"sub": "encoded_username"},
        SERVER_CONFIG.AUTH_SECRET_KEY,
        algorithm=SERVER_CONFIG.AUTH_ALGORITHM,
    )

    result = await get_current_active_user(db=mocked_manager, token=new_token)
    assert result.username == "encoded_username"
    assert mocked_manager.good_user
    assert not mocked_manager.bad_user

    mocked_manager.good_user = False

    mocked_manager = MockedManager()
    new_token = jwt.encode(
        {"sub": "bad_username"},
        SERVER_CONFIG.AUTH_SECRET_KEY,
        algorithm=SERVER_CONFIG.AUTH_ALGORITHM,
    )
    with pytest.raises(HTTPException) as excinfo:
        result = await get_current_active_user(db=mocked_manager, token=new_token)

    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert not mocked_manager.good_user
    assert mocked_manager.bad_user
