"""
Module for all used error objects / messages.
"""
from fastapi import HTTPException, status

# This is not optimal but black and flake8 are having a
# stubborness contest about line limit and how to split
# strings into line that I can't spend more than 10 min
# trying to solve.
exception_details = "Resources do not exist "
exception_details += "or you are not authorized"
exception_details += "to access them."

UNAUTHORIZED_RESOURCE_ERROR = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=exception_details,
    headers={"WWW-Authenticate": "Bearer"},
)

INCORRECT_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password.",
    headers={"WWW-Authenticate": "Bearer"},
)

INCORRECT_JSONWEBTOKEN_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

PREEXISTING_USERNAME_ERROR = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Username already exist in the server.",
    headers={"WWW-Authenticate": "Bearer"},
)

PREEXISTING_EMAIL_ERROR = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Email already exist in the server.",
    headers={"WWW-Authenticate": "Bearer"},
)

UNMODIFIABLE_TRAIT_ERROR = HTTPException(
    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
    detail="Only username or role attributes may be modified.",
    headers={"WWW-Authenticate": "Bearer"},
)

UNRECOGNIZED_CELEBRITY_ERROR = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Recognition of photo provided does match user name.",
    headers={"WWW-Authenticate": "Bearer"},
)
