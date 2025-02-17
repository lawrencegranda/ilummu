"""Test utility functions for generating JWT tokens and other test helpers."""

# Standard Library imports
from typing import Dict, Any, List

# Local Application imports
from edify.models import User
from edify.utils.constants import primitives


def get_jwt_header(user: User) -> dict:
    """Get JWT authorization header for a user."""
    access_token = user.get_access_token()
    return {"Authorization": f"Bearer {access_token}"}


def compare_dicts(
    obj1: Dict[str, Any], obj2: Dict[str, Any], keys_to_skip: List[str] | None = None
) -> None:
    """Compare two dictionaries."""
    if keys_to_skip is None:
        keys_to_skip = []

    for (k1, v1), (k2, v2) in zip(obj1.items(), obj2.items()):
        assert k1 == k2, f"Keys are not equal ({k1} != {k2})"
        if k1 in keys_to_skip or not isinstance(v1, primitives):
            continue
        assert v1 == v2, f"Values for '{k1}' are not equal ({v1} != {v2})"
