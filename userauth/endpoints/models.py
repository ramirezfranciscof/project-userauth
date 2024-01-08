"""
Module with the definition for objects returned by the REST API.
"""
from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict

from userauth.common.roles import Role
from userauth.database import LoginEntry, UserEntry


class UserData(BaseModel):
    username: str
    surname: str
    name: str
    email: str


class User(UserData):
    uuid: UUID4
    role: Role

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_dbentry(cls, user_entry: UserEntry) -> "User":
        """Constructor from a database user entry.

        Necessary to explicitly construct the User.
        """
        new_object = cls(
            uuid=user_entry.uuid,
            role=user_entry.role,
            username=user_entry.username,
            email=user_entry.email,
            name=user_entry.name,
            surname=user_entry.surname,
        )
        return new_object


class LoginRecord(BaseModel):
    uuid: UUID4
    user_uuid: UUID4
    login_time: datetime

    @classmethod
    def from_dbentry(cls, database_entry: LoginEntry) -> "LoginRecord":
        """Constructor from a database login entry.

        Necessary to explicitly construct the Login record.
        """
        new_object = cls(
            uuid=database_entry.uuid,
            user_uuid=database_entry.user,
            login_time=database_entry.ctime,
        )
        return new_object
