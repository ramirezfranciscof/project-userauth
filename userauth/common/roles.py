"""
Module for the roles.

This needs to be separated from the policy enforcer since
the policy enforcers requires the definition of User and
User require the definitions of Role.
"""
from enum import Enum


class Role(Enum):
    normal = "normal user"
    admin = "admin user"
    celebrity = "celebrity user"
