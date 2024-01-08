"""
Module with the database ORM models.
"""
from sqlalchemy import TIMESTAMP, Column, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func

from userauth.common.roles import Role


class Base(DeclarativeBase):
    pass


class UserEntry(Base):
    __tablename__ = "users"

    # Public properties
    uuid = Column(Uuid, primary_key=True, index=True)
    role = Column(Enum(Role))
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    surname = Column(String, index=True)
    ctime = Column(TIMESTAMP, server_default=func.now())

    # Private properties
    hashed_password = Column(String)


class LoginEntry(Base):
    __tablename__ = "logins"

    uuid = Column(Uuid, primary_key=True, index=True)
    user = Column(Uuid, ForeignKey("users.uuid"), nullable=False)
    ctime = Column(TIMESTAMP, server_default=func.now())
