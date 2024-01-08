"""
Module for access policy management.

This needs to be separated from the Role definition since
the policy enforcers requires the definition of User and
User require the definitions of Role.
"""
from typing import Union

from userauth.common.roles import Role
from userauth.endpoints.models import LoginRecord, User


class PolicyEnforcer:
    """
    Class with methods to enforce access policies for a given user.
    """

    def __init__(self, user: User):
        """Initialize enforcer for a giver user."""
        self._user = user

    def can_see_all(self):
        """Check access rights to see everything in the database."""
        return self._user.role == Role.admin

    def can_see_object(self, object: Union[User, LoginRecord]):
        """Check access rights to see a given object."""
        if self._user.role == Role.admin:
            return True

        if isinstance(object, User):
            if self._user.uuid == object.uuid:
                return True

        if isinstance(object, LoginRecord):
            if self._user.uuid == object.user_uuid:
                return True

        return False

    def can_update_username(self, object: User):
        """Check access rights to update the username of a given User."""
        if self._user.role == Role.admin:
            return True

        if self._user.uuid == object.uuid:
            return True

        return False

    def can_update_role(self, object: User):
        """Check access rights to update the role of a given User."""
        return self._user.role == Role.admin

    def can_delete(self, object: User):
        """Check access rights to delete a given User."""
        return self._user.uuid == object.uuid

    def can_claim_celebrity(self, celebrity_name: str, probability: float):
        """Check if similarity is enough to claim celebrity role."""

        full_name = f"{self._user.name} {self._user.surname}"
        if full_name != celebrity_name:
            return False

        return probability > 0.95
