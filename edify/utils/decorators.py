from functools import wraps
from flask import jsonify, current_app, redirect, url_for
from http import HTTPStatus
from typing import Callable, List, Union
from flask_login import UserMixin
from edify import jwt, db
from edify.models import User, Question
from edify.utils.constants import AuthLevelEnum, ErrorType
from edify.utils.utils import error_response
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, current_user


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


def manager_required(minimum_manager_level: AuthLevelEnum) -> Callable:
    """
    Decorator for managing access to endpoints based on manager level.
    """

    def decorator(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args: tuple, **kwargs: dict) -> Union[tuple, UserMixin]:
            if not isinstance(current_user, UserMixin):
                return error_response(
                    "User not authenticated", ErrorType.USER_NOT_AUTHENTICATED
                )
            if current_user.auth_level < minimum_manager_level.value:
                return error_response("Not ", HTTPStatus.FORBIDDEN)
            return function(*args, **kwargs)

        return wrapper

    return decorator


def role_required(roles: List[AuthLevelEnum]) -> Callable:
    """
    Decorator for managing access to endpoints based on user roles.
    """

    def decorator(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args: tuple, **kwargs: dict) -> Union[tuple, UserMixin]:
            if not isinstance(current_user, UserMixin):
                return error_response(
                    "User not authenticated", ErrorType.USER_NOT_AUTHENTICATED
                )
            if current_user.auth_level not in roles:
                return error_response(
                    "User is not allowed to access",
                    ErrorType.ACCESS_FORBIDDEN,
                    HTTPStatus.FORBIDDEN,
                )
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
            return error_response("App in maintenance mode", ErrorType.MAINTENANCE)
        return function(*args, **kwargs)

    return decorator


def no_token_allowed(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        verify_jwt_in_request(optional=True)

        user_id = get_jwt_identity()
        if not user_id:
            return f(*args, **kwargs)

        if User.query.get(user_id):
            return redirect(url_for("frontend.dashboard"))

        return f(*args, **kwargs)

    return decorator


def author_required(arg_name: str):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request(optional=False)

            # Check for the argument in kwargs first, then in args
            if arg_name in kwargs:
                value = kwargs[arg_name]
            elif arg_name in f.__code__.co_varnames:
                arg_index = f.__code__.co_varnames.index(arg_name)
                value = args[arg_index]
            else:
                return error_response(
                    "Question id argument must be passed in", ErrorType.BAD_REQUEST
                )

            # Check if the value is an int
            if not isinstance(value, int):
                return error_response(
                    "Question id argument must be an int", ErrorType.BAD_REQUEST
                )

            user_id = get_jwt_identity()
            if not user_id or not User.query.get(user_id):
                return error_response("User not found", ErrorType.USER_NOT_FOUND)

            id_question = value
            question = db.session.query(Question).get(id_question)
            if not question:
                return error_response("Question not found", ErrorType.NOT_FOUND)

            if question.user_id != user_id:
                return error_response(
                    "User is not the author of the question", ErrorType.UNAUTHORIZED
                )

            return f(*args, **kwargs)

        return wrapper

    return decorator
