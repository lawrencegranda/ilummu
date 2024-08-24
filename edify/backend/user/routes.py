# Standard Library imports
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Optional, Any, Tuple

# Third-Party Framework imports
from flask import Blueprint, url_for, jsonify, current_app, request
from flask import typing as flask_typing
from flask_jwt_extended import (
    jwt_required,
    current_user,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from flask_login import UserMixin
from webargs import fields, validate
from webargs.flaskparser import use_args

# Local Application imports
from edify import db
from edify.models import (
    Notification,
    AcademicField,
    Method,
    TimeInterval,
    Course,
    School,
    Major,
    User,
    Question,
    Offer,
    NotificationType,
)
from edify.utils.constants import (
    ErrorType,
    AuthLevelEnum,
    SupportedLanguagesEnum,
    NotificationTypeEnum,
)
from edify.utils.utils import (
    error_response,
    validate_date,
    validate_email,
    validate_phone,
    generate_funny_username,
    format_phone,
)
from edify.backend.user.utils import get_current_user, generate_refresh_token


# -----------------------------------------------------------------------------
# Route Blueprint
# -----------------------------------------------------------------------------
# Endpoint: /backend/user/
user = Blueprint("user", __name__, url_prefix="/user")


# -----------------------------------------------------------------------------
# Blueprint Endpoints (user)
# -----------------------------------------------------------------------------


# Endpoint: /backend/user/logout
@user.route("/logout", methods=["POST"])
def logout() -> flask_typing.ResponseReturnValue:
    """
    Endpoint to log out a user.

    Returns:
        Response: JSON response indicating successful logout.
    """
    response = jsonify({"message": "Successfully logged out."})
    unset_jwt_cookies(response)
    return (response, HTTPStatus.OK)


# Endpoint: /backend/user/refresh
@user.route("/refresh", methods=["GET", "POST"])
@jwt_required(refresh=True)
def refresh() -> flask_typing.ResponseReturnValue:
    """
    Endpoint to refresh the user's access token.

    Returns:
        Response: JSON response with the new access token.
    """
    user = get_current_user()
    print(f"Refreshing token... User {user.id}")
    token = user.get_access_token()
    db.session.commit()
    response = jsonify({"access_token": token})
    set_access_cookies(response, token)
    return (response, HTTPStatus.OK)


# Endpoint: /backend/user
@user.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_user() -> flask_typing.ResponseReturnValue:
    """
    Endpoint to get the current user's information.

    Returns:
        Response: JSON response with the user's information or None if not found.
    """
    user = get_current_user()
    if user:
        return jsonify(user.to_dict(simplified=False)), HTTPStatus.OK
    return jsonify(None), HTTPStatus.NOT_FOUND


# Endpoint: /backend/user/login
@user.route("/login", methods=["POST"])
@use_args(
    {
        "email": fields.Email(required=True),
        "password": fields.Str(required=True),
        "remember": fields.Boolean(required=False),
    }
)
def login(args) -> flask_typing.ResponseReturnValue:
    """
    Endpoint to log in a user.

    Args:
        args (dict): The login arguments containing email, password, and remember flag.

    Returns:
        Response: JSON response with the access token and user information.
    """
    # Get the user corresponding to the email that is logging in
    user = db.session.query(User).filter_by(email=args["email"], is_mock=False).first()

    # Check if user exists and if the given password is correct
    if not user or not user.check_password(args["password"]):
        return error_response(
            "Incorrect email or password", ErrorType.INCORRECT_CREDENTIALS
        )

    # # Uncomment these lines to enable email and phone verification checks
    # if user.mail_is_verified is False:
    #     return error_response("Email not verified", ErrorType.USER_NOT_VERIFIED)
    # if user.phone_is_verified is False:
    #     return error_response("Phone not verified", ErrorType.USER_NOT_VERIFIED)

    # Generate and commit the access token for the user
    access_token = user.get_access_token()
    db.session.commit()

    if user.auth_level in [AuthLevelEnum.SCHOOL_ADMIN, AuthLevelEnum.SUPER_ADMIN]:
        # Additional logic for admin users (if needed)
        pass

    response = jsonify(
        {"access_token": access_token, "user": user.to_dict(simplified=True)}
    )
    set_access_cookies(response, access_token)

    if "remember" in args and args["remember"]:
        set_refresh_cookies(
            response,
            generate_refresh_token(user),
            max_age=current_app.config["JWT_REFRESH_TOKEN_EXPIRES"],
        )

    return (response, HTTPStatus.OK)


# Endpoint: /backend/user/new
@user.route("/new", methods=["POST"])
@use_args(
    {
        "firstname": fields.Str(
            required=False, validate=validate.Length(min=2, max=20)
        ),
        "lastname": fields.Str(required=False, validate=validate.Length(min=2, max=35)),
        "email": fields.Email(required=True, validate=validate.Length(min=3, max=120)),
        "phone": fields.Str(required=True, validate=validate.Length(min=12, max=19)),
        "password": fields.Str(required=True),
        "school": fields.Str(required=False),
        "major": fields.Str(required=True),
        "graduation": fields.Date(required=True),
        "language": fields.Str(required=False),
        "remember": fields.Boolean(required=False),
    }
)
def signup(args) -> flask_typing.ResponseReturnValue:
    """
    Endpoint to create a new user.

    Args:
        args (dict): The user creation arguments.

    Returns:
        Response: JSON response with the access token and user information.
    """
    # Trim all string values in args
    for key, value in args.items():
        if isinstance(value, str):
            args[key] = value.strip()

    if not validate_phone(args["phone"]):
        return error_response(
            f"Invalid phone format {args['phone']}", ErrorType.BAD_REQUEST
        )
    args["phone"] = format_phone(args["phone"])

    if not validate_email(args["email"]):
        return error_response("Invalid email format.", ErrorType.BAD_REQUEST)

    # Check if email is already taken
    user = db.session.query(User).filter_by(email=args["email"]).first()
    if user:
        return error_response("Email is already taken", ErrorType.BAD_REQUEST)

    # Check if phone is already taken
    user = db.session.query(User).filter_by(phone=args["phone"]).first()
    if user:
        return error_response("Phone is already taken", ErrorType.BAD_REQUEST)

    # Determine the user's language preference
    if "language" in args and args["language"]:
        language = args["language"]
    else:
        language = SupportedLanguagesEnum.ENGLISH

    if language not in SupportedLanguagesEnum.keys():
        return error_response(
            f"Invalid language: {language} is not one of {' '.join(SupportedLanguagesEnum.keys())}",
            ErrorType.BAD_REQUEST,
        )

    # Determine the user's school
    if "school" in args and args["school"]:
        school = db.session.query(School).filter_by(name=args["school"]).first()
    else:
        school = db.session.query(School).filter_by(name="Cornell University").first()

    if not school:
        return error_response("Invalid school.", ErrorType.BAD_REQUEST)

    # Determine the user's major
    major = (
        db.session.query(Major)
        .filter_by(name=args["major"], school_id=school.id)
        .first()
    )
    if not major:
        return error_response("Invalid Major.", ErrorType.BAD_REQUEST)

    # Hash password before storing it in the db for privacy purposes
    hashed_password = User.hash_password(args["password"])

    # Generate a unique and funny username
    n = 3
    counter = 0
    username = generate_funny_username(n)
    while db.session.query(User).filter_by(username=username).first():
        if counter > 10:
            n += 1
        if counter > 100:
            return error_response("Ran out of usernames.", ErrorType.INTERNAL_ERROR)
        username = generate_funny_username(n)

    if "firstname" not in args or not args["firstname"]:
        args["firstname"] = username
    if "lastname" not in args or not args["lastname"]:
        args["lastname"] = username

    # Create new user in the User table
    user = User(
        username=username,
        firstname=args["firstname"],
        lastname=args["lastname"],
        email=args["email"],
        phone=args["phone"],
        password=hashed_password,
        school_id=school.id,
        major_id=major.id,
        graduation=args["graduation"],
        language=language,
    )

    # Add new user to the database
    db.session.add(user)
    db.session.commit()

    # Generate the access token for the user
    access_token = user.get_access_token()

    # Create a notification for the new user
    notif = Notification(
        type=NotificationTypeEnum.ACCOUNT_CREATED,
        message=f"Welcome {username}!",
        user_id=user.id,
    )
    db.session.add(notif)
    db.session.commit()

    response = jsonify(
        {"access_token": access_token, "user": user.to_dict(simplified=True)}
    )
    set_access_cookies(response, access_token)

    if "remember" in args and args["remember"]:
        set_refresh_cookies(
            response,
            generate_refresh_token(user),
            max_age=current_app.config["JWT_REFRESH_TOKEN_EXPIRES"],
        )

    return (response, HTTPStatus.CREATED)


# Endpoint: /backend/user/reset-email
@user.route("/reset-email", methods=["POST"])
@use_args(
    {
        "email": fields.Email(required=True),
    }
)
def reset_email(args) -> flask_typing.ResponseReturnValue:
    """
    Endpoint to reset send an email to reset password.

    Args:
        args (dict): The login arguments containing email.

    Returns:
        Response: Send email.
    """
    # Get the user corresponding to the email that is logging in
    user = db.session.query(User).filter_by(email=args["email"], is_mock=False).first()

    # Check if user exists and if the given password is correct
    if not user:
        return error_response(
            "Email not found. Register for an account.", ErrorType.INCORRECT_CREDENTIALS
        )

    return error_response("Not implemented.", ErrorType.NOT_IMPLEMENTED)


# Endpoint: /backend/user/reset-password
@user.route("/reset-password", methods=["POST"])
@use_args(
    {
        "password": fields.Str(required=True),
        "token": fields.Str(required=True),
    }
)
def reset_password(args) -> flask_typing.ResponseReturnValue:
    """
    Endpoint to reset a password.

    Args:
        args (dict): The login arguments containing email.

    Returns:
        Response: Tuple
    """
    # Get the user corresponding to the email that is logging in
    user = db.session.query(User).filter_by(email=args["email"], is_mock=False).first()

    # Check if user exists and if the given password is correct
    if not user:
        return error_response(
            "Email not found. Register for an account.", ErrorType.INCORRECT_CREDENTIALS
        )

    return error_response("Not implemented.", ErrorType.NOT_IMPLEMENTED)
