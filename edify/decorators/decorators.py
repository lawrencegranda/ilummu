from functools import wraps
from flask import jsonify, current_app
from http import HTTPStatus
from typing import Callable, List, Union
from flask_login import UserMixin
from flask_jwt_extended import jwt
from edify.models import User
from edify.utils.constants import AuthLevel
from edify.utils.utils import error_response


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data) -> "User":
    """
    Callback function for Flask JWT Extended user lookup.

    This function retrieves a user object from the database whenever a protected
    route is accessed.

    This should return any python object on a successful lookup, or None if the
    lookup failed (for example, if the user has been deleted from the database).
    """
    identity = jwt_data["sub"]
    return User.query.get(int(identity))


def manager_required(minimum_manager_level: AuthLevel) -> Callable:
    """
    Decorator for managing access to endpoints based on manager level.
    """

    def decorator(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args: tuple, **kwargs: dict) -> Union[tuple, UserMixin]:
            if not isinstance(current_user, UserMixin):
                return error_response(
                    "User not authenticated",
                    "USER_NOT_AUTHENTICATED",
                    HTTPStatus.UNAUTHORIZED,
                )
            if current_user.auth_level < minimum_manager_level.value:
                return error_response("Not ", HTTPStatus.FORBIDDEN)
            return function(*args, **kwargs)

        return wrapper

    return decorator


def role_required(roles: List[AuthLevel]) -> Callable:
    """
    Decorator for managing access to endpoints based on user roles.
    """

    def decorator(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args: tuple, **kwargs: dict) -> Union[tuple, UserMixin]:
            if not isinstance(current_user, UserMixin):
                return error_response("User not authenticated", HTTPStatus.UNAUTHORIZED)
            if current_user.auth_level not in roles:
                return error_response("Access forbidden", HTTPStatus.FORBIDDEN)
            return function(*args, **kwargs)

        return wrapper

    return decorator


def maintenance_mode(function: Callable) -> Callable:
    """
    Decorator to enable/disable routes based on Maintenance Mode.
    """

    @wraps(function)
    def decorator(*args: tuple, **kwargs: dict) -> Union[tuple, UserMixin]:
        if current_app.config.get("MAINTENANCE_MODE", False):
            return error_response("App in maintenance mode", HTTPStatus.FORBIDDEN)
        return function(*args, **kwargs)

    return decorator
