"""
Module with the functions and endpoints for authentication.
"""
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from userauth.common.config import SERVER_CONFIG
from userauth.database import DatabaseManager, get_database_manager
from userauth.endpoints.models import User

from .errors import (
    INCORRECT_CREDENTIALS_ERROR,
    INCORRECT_JSONWEBTOKEN_ERROR,
    PREEXISTING_EMAIL_ERROR,
    PREEXISTING_USERNAME_ERROR,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class TokenPackage(BaseModel):
    access_token: str
    token_type: str


def create_access_token(
    data: dict,
    expires_delta: timedelta = timedelta(minutes=15),
):
    """Create the JWT encoded string with the data and the expiration time."""
    to_encode = data.copy()
    expiration_time = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expiration_time})
    encoded_jwt = jwt.encode(
        to_encode,
        SERVER_CONFIG.AUTH_SECRET_KEY,
        algorithm=SERVER_CONFIG.AUTH_ALGORITHM,
    )
    return encoded_jwt


authentication = APIRouter(tags=["Authentication"])


@authentication.post("/token", response_model=TokenPackage)
async def login_for_access_token(
    db: DatabaseManager = Depends(get_database_manager),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """Log in using username and password."""

    user = await db.authenticate_user(form_data.username, form_data.password)

    if user is None:
        raise INCORRECT_CREDENTIALS_ERROR

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=SERVER_CONFIG.AUTH_EXPIRATION_MINS),
    )

    await db.record_login(user)
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_active_user(
    db: DatabaseManager = Depends(get_database_manager),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Return the current active user from authentication."""
    try:
        payload = jwt.decode(
            token,
            SERVER_CONFIG.AUTH_SECRET_KEY,
            algorithms=[SERVER_CONFIG.AUTH_ALGORITHM],
        )
        username: str = payload.get("sub")
        if username is None:
            raise INCORRECT_JSONWEBTOKEN_ERROR

    except JWTError:
        raise INCORRECT_JSONWEBTOKEN_ERROR

    user = await db.get_user(username=username)
    if user is None:
        raise INCORRECT_JSONWEBTOKEN_ERROR

    return user


@authentication.post("/users", response_model=User, status_code=201)
async def post_users(
    # user_data: UserData, -> This breaks swagger ui
    username: str,
    password: Annotated[str, Form(format="password")],
    email: Annotated[str, Form(format="email")],
    name: str,
    surname: str,
    dbmanager: DatabaseManager = Depends(get_database_manager),
):
    """Register a new user."""

    existing_user = await dbmanager.get_user(username=username)
    if existing_user is not None:
        raise PREEXISTING_USERNAME_ERROR

    existing_user = await dbmanager.get_user(email=email)
    if existing_user is not None:
        raise PREEXISTING_EMAIL_ERROR

    created_user = await dbmanager.create_user(
        username,
        password,
        email,
        name,
        surname,
    )

    return created_user
