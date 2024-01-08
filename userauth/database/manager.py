"""
Module containing the database manager.
"""
from typing import List, Optional
from uuid import UUID, uuid4

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from userauth.common.roles import Role

from .models import LoginEntry, UserEntry

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password):
    return pwd_context.hash(password)


class DatabaseManager:
    """
    Class to wrap the current session and database procedures.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the manager with a scoped async session."""
        self._session = session

    async def get_users(self) -> List[UserEntry]:
        """Get all users from the database."""
        querystr = select(UserEntry)
        results = await self._session.execute(querystr)
        results = [result[0] for result in results]
        return results

    async def get_user(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        uuid: Optional[UUID] = None,
    ) -> UserEntry:
        """Get a single user from the database.

        The user must be identified by either its username,
        its email or its uuid (only one of these).
        """
        arguments_provided = 0
        arguments_provided += 0 if username is None else 1
        arguments_provided += 0 if email is None else 1
        arguments_provided += 0 if uuid is None else 1

        if arguments_provided > 1:
            raise ValueError(
                "You must provide only one of: username, email, uuid.",
            )

        if username is not None:
            querystr = select(UserEntry).filter_by(username=username)

        elif email is not None:
            querystr = select(UserEntry).filter_by(email=email)

        elif uuid is not None:
            querystr = select(UserEntry).filter_by(uuid=uuid)

        else:
            raise ValueError(
                "You must provide at least one of: username, email, uuid.",
            )

        results = await self._session.execute(querystr)
        result = results.scalars().first()
        return result

    async def authenticate_user(
        self,
        username: str,
        password: str,
    ) -> Optional[UserEntry]:
        """Authenticate the user.

        Return the user if authenticated, otherwise return None.
        """
        user = await self.get_user(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def create_user(
        self,
        username: str,
        password: str,
        email: str,
        name: str = "John",
        surname: str = "Doe",
    ):
        """Create a new user.

        The pre-existence of the username and password should have
        already been tested.
        """
        new_user = UserEntry(
            uuid=uuid4(),
            role=Role.normal,
            username=username,
            email=email,
            name=name,
            surname=surname,
            hashed_password=hash_password(password),
        )

        self._session.add(new_user)
        await self._session.commit()
        await self._session.refresh(new_user)

        return new_user

    async def record_login(self, user: UserEntry):
        """Create record of a session login."""
        new_login = LoginEntry(
            uuid=uuid4(),
            user=user.uuid,
        )

        self._session.add(new_login)
        await self._session.commit()
        await self._session.refresh(new_login)

        return new_login

    async def get_login(self, uuid: UUID) -> LoginEntry:
        """Get a single login record from the database."""
        querystr = select(LoginEntry).filter_by(uuid=uuid)
        result = await self._session.execute(querystr)
        return result.scalars().first()

    async def get_logins(self, user_uuid: Optional[UUID]) -> List[LoginEntry]:
        """Get a list of login records from the database.

        If a user uuid is provided, it will only be logins from
        said user.
        """
        if user_uuid is None:
            querystr = select(LoginEntry)
        else:
            querystr = select(LoginEntry).filter_by(user=user_uuid)
        results = await self._session.execute(querystr)
        results = [result[0] for result in results]
        return results

    async def delete_user(self, uuid: UUID) -> None:
        """Delete a user and all login records from the database."""
        user = await self.get_user(uuid=uuid)
        logins = await self.get_logins(user_uuid=uuid)

        await self._session.delete(user)
        for login in logins:
            await self._session.delete(login)

        await self._session.commit()

    async def update_user(
        self,
        uuid: UUID,
        new_role: Optional[Role] = None,
        new_username: Optional[str] = None,
    ) -> UserEntry:
        """Update user information (username or role)."""
        user = await self.get_user(uuid=uuid)

        if new_username is not None:
            user.username = new_username

        if new_role is not None:
            user.role = new_role

        await self._session.commit()
        user = await self.get_user(uuid=uuid)
        return user
