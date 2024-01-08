"""
Endpoints for the API.
"""
import base64
from pathlib import Path
from typing import Annotated, List

from fastapi import APIRouter, Depends, File
from pydantic import UUID4

from userauth.common.policies import PolicyEnforcer
from userauth.common.roles import Role
from userauth.database import DatabaseManager, get_database_manager
from userauth.endpoints.models import LoginRecord, User
from userauth.picmodel import CelebDetector

from .auth import get_current_active_user
from .errors import (
    PREEXISTING_USERNAME_ERROR,
    UNAUTHORIZED_RESOURCE_ERROR,
    UNMODIFIABLE_TRAIT_ERROR,
    UNRECOGNIZED_CELEBRITY_ERROR,
)

resources = APIRouter(tags=["Resources"])


###############################################################################
# ACTIVE USER SHORTCUTS
###############################################################################


@resources.get("/users/me", response_model=User)
async def get_users_me(active_user: User = Depends(get_current_active_user)):
    """Get the active user."""
    return active_user


@resources.get("/users/me/logins", response_model=List[LoginRecord])
async def get_users_me_logins(
    active_user: User = Depends(get_current_active_user),
    dbmanager: DatabaseManager = Depends(get_database_manager),
):
    """Get the loggins for the active user."""
    login_entries = await dbmanager.get_logins(user_uuid=active_user.uuid)

    logins_list = list()
    for login_entry in login_entries:
        login = LoginRecord.from_dbentry(login_entry)
        logins_list.append(login)

    return logins_list


@resources.get("/users/me/logins/{login_id}", response_model=LoginRecord)
async def get_users_me_logins_id(
    login_id: UUID4,
    active_user: User = Depends(get_current_active_user),
    dbmanager: DatabaseManager = Depends(get_database_manager),
):
    """Get a specific loggin for the active user."""
    output = await get_logins_id(
        login_id,
        active_user=active_user,
        dbmanager=dbmanager,
    )
    return output


###############################################################################
# USER ENDPOINTS
###############################################################################


@resources.get("/users", response_model=List[User])
async def get_users(
    active_user: User = Depends(get_current_active_user),
    dbmanager: DatabaseManager = Depends(get_database_manager),
):
    """Get user by ID."""
    active_user_rights = PolicyEnforcer(active_user)
    if not active_user_rights.can_see_all():
        raise UNAUTHORIZED_RESOURCE_ERROR
    all_users = await dbmanager.get_users()
    return all_users


@resources.get("/users/{user_id}", response_model=User)
async def get_users_id(
    user_id: UUID4,
    active_user: User = Depends(get_current_active_user),
    dbmanager: DatabaseManager = Depends(get_database_manager),
):
    """Get user by ID."""

    requested_user = await dbmanager.get_user(uuid=user_id)
    if requested_user is None:
        raise UNAUTHORIZED_RESOURCE_ERROR
    requested_user = User.from_dbentry(requested_user)

    active_user_rights = PolicyEnforcer(active_user)
    if not active_user_rights.can_see_object(requested_user):
        raise UNAUTHORIZED_RESOURCE_ERROR

    return requested_user


@resources.get("/users/{user_id}/logins", response_model=List[LoginRecord])
async def get_users_id_logins(
    user_id: UUID4,
    active_user: User = Depends(get_current_active_user),
    dbmanager: DatabaseManager = Depends(get_database_manager),
):
    """Get all login records for a given user."""

    requested_user = await dbmanager.get_user(uuid=user_id)
    if requested_user is None:
        raise UNAUTHORIZED_RESOURCE_ERROR
    requested_user = User.from_dbentry(requested_user)

    active_user_rights = PolicyEnforcer(active_user)
    if not active_user_rights.can_see_object(requested_user):
        raise UNAUTHORIZED_RESOURCE_ERROR

    login_entries = await dbmanager.get_logins(user_uuid=user_id)

    logins_list = list()
    for login_entry in login_entries:
        login = LoginRecord.from_dbentry(login_entry)
        logins_list.append(login)

    return logins_list


@resources.get(
    "/users/{user_id}/logins/{login_id}",
    response_model=LoginRecord,
)
async def get_users_id_logins_id(
    user_id: UUID4,
    login_id: UUID4,
    active_user: User = Depends(get_current_active_user),
    dbmanager: DatabaseManager = Depends(get_database_manager),
):
    """Get login record from a user by ID."""

    requested_user = await dbmanager.get_user(uuid=user_id)
    if requested_user is None:
        raise UNAUTHORIZED_RESOURCE_ERROR
    requested_user = User.from_dbentry(requested_user)

    active_user_rights = PolicyEnforcer(active_user)
    if not active_user_rights.can_see_object(requested_user):
        raise UNAUTHORIZED_RESOURCE_ERROR

    logins_list = await get_logins_id(
        login_id=login_id,
        active_user=active_user,
        dbmanager=dbmanager,
    )

    return logins_list


###############################################################################
# VALIDATE CELEBRITIES AND UPDATE / DELETE USERS
###############################################################################


@resources.post("/users/{user_id}/validate_photo", response_model=User)
async def post_users_id_validate(
    file: Annotated[bytes, File()],
    active_user: User = Depends(get_current_active_user),
    dbmanager: DatabaseManager = Depends(get_database_manager),
):
    """Action endpoint to auto-validate celebrity users."""
    encoded_img = base64.b64encode(file)
    model_data_path = Path(__file__).parent.parent / "picmodel" / "celebs.h5"
    celeb_detector = CelebDetector(model_data_path)

    # Correct usage:
    #(celebrity_name, prob) = celeb_detector.predicta(encoded_img)

    # Temporary patch that always accepts celebrity
    celebrity_name = f"{active_user.name} {active_user.surname}"
    prob = 0.96
    (celebrity_name, prob) = celeb_detector.predicta(encoded_img, celebrity_name, prob)

    active_user_rights = PolicyEnforcer(active_user)
    if not active_user_rights.can_claim_celebrity(celebrity_name, prob):
        raise UNRECOGNIZED_CELEBRITY_ERROR

    updated_user = await dbmanager.update_user(
        uuid=active_user.uuid,
        new_role=Role.celebrity,
    )
    return updated_user


@resources.patch("/users/{user_id}", response_model=User)
async def update_users_id(
    user_id: UUID4,
    updated_user: User,
    active_user: User = Depends(get_current_active_user),
    dbmanager: DatabaseManager = Depends(get_database_manager),
):
    """Update user username / role by ID."""

    requested_user = await dbmanager.get_user(uuid=user_id)
    if requested_user is None:
        raise UNAUTHORIZED_RESOURCE_ERROR
    requested_user = User.from_dbentry(requested_user)

    active_user_rights = PolicyEnforcer(active_user)
    if not active_user_rights.can_see_object(requested_user):
        raise UNAUTHORIZED_RESOURCE_ERROR

    if requested_user.username != updated_user.username:
        if not active_user_rights.can_update_username(requested_user):
            raise UNAUTHORIZED_RESOURCE_ERROR
        existing_user = await dbmanager.get_user(username=updated_user.username)
        if existing_user is not None:
            raise PREEXISTING_USERNAME_ERROR

    if requested_user.role != updated_user.role:
        if not active_user_rights.can_update_role(requested_user):
            raise UNMODIFIABLE_TRAIT_ERROR

    other_modifs = False
    other_modifs |= requested_user.uuid != updated_user.uuid
    other_modifs |= requested_user.name != updated_user.name
    other_modifs |= requested_user.surname != updated_user.surname
    other_modifs |= requested_user.email != updated_user.email
    if other_modifs:
        raise UNMODIFIABLE_TRAIT_ERROR

    updated_user = await dbmanager.update_user(
        uuid=user_id,
        new_role=updated_user.role,
        new_username=updated_user.username,
    )
    updated_user = User.from_dbentry(updated_user)
    return updated_user


@resources.delete("/users/{user_id}", status_code=204)
async def delete_users_id(
    user_id: UUID4,
    active_user: User = Depends(get_current_active_user),
    dbmanager: DatabaseManager = Depends(get_database_manager),
) -> None:
    """Delete user by ID."""

    requested_user = await dbmanager.get_user(uuid=user_id)
    if requested_user is None:
        raise UNAUTHORIZED_RESOURCE_ERROR
    requested_user = User.from_dbentry(requested_user)

    active_user_rights = PolicyEnforcer(active_user)
    if not active_user_rights.can_delete(requested_user):
        raise UNAUTHORIZED_RESOURCE_ERROR

    await dbmanager.delete_user(uuid=user_id)


###############################################################################
# LOGIN ENDPOINTS
###############################################################################


@resources.get("/logins", response_model=List[LoginRecord])
async def get_logins(
    active_user: User = Depends(get_current_active_user),
    dbmanager: DatabaseManager = Depends(get_database_manager),
):
    """Get all login records from the database."""
    active_user_rights = PolicyEnforcer(active_user)
    if not active_user_rights.can_see_all():
        raise UNAUTHORIZED_RESOURCE_ERROR

    login_entries = await dbmanager.get_logins(user_uuid=None)
    logins_list = list()
    for login_entry in login_entries:
        login = LoginRecord.from_dbentry(login_entry)
        logins_list.append(login)

    return logins_list


@resources.get("/logins/{login_id}", response_model=LoginRecord)
async def get_logins_id(
    login_id: UUID4,
    active_user: User = Depends(get_current_active_user),
    dbmanager: DatabaseManager = Depends(get_database_manager),
):
    """Get a single login record by ID."""

    requested_resource = await dbmanager.get_login(uuid=login_id)
    if requested_resource is None:
        raise UNAUTHORIZED_RESOURCE_ERROR

    requested_resource = LoginRecord.from_dbentry(requested_resource)

    active_user_rights = PolicyEnforcer(active_user)
    if not active_user_rights.can_see_object(requested_resource):
        raise UNAUTHORIZED_RESOURCE_ERROR

    return requested_resource
