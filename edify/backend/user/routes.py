from flask import Blueprint, url_for, jsonify, current_app, request
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
from edify.utils.constants import ErrorType, AuthLevelEnum, SupportedLanguagesEnum
from edify.utils.utils import (
    error_response,
    validate_date,
    validate_email,
    validate_phone,
    generate_funny_username,
    format_phone,
)
from datetime import datetime, timedelta
from edify.models import (
    User,
    Question,
    Offer,
    Notification,
    AcademicField,
    Method,
    TimeInterval,
    Course,
    School,
    NotificationType,
    Major,
)
from edify import db
from http import HTTPStatus
from typing import Optional, Any


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def get_current_user() -> Optional[User]:
    return current_user if isinstance(current_user, UserMixin) else None


def generate_access_token(user: User) -> Any:
    access_token = user.get_reset_token()
    user.token = access_token
    user.token_last_refresh = datetime.utcnow()
    return access_token


def generate_refresh_token(user: User) -> Any:
    refresh_token = user.get_refresh_token()
    return refresh_token


# -----------------------------------------------------------------------------
# Route Blueprint
# -----------------------------------------------------------------------------
# Endpoint: /user/
user = Blueprint("user", __name__, url_prefix="/user")


# -----------------------------------------------------------------------------
# Blueprint Endpoints (user)
# -----------------------------------------------------------------------------


# Endpoint: /user/logout
@user.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """Endpoint to log out a user."""

    response = jsonify({"message": "Successfully logged out."})
    unset_jwt_cookies(response)

    return (response, HTTPStatus.OK)


# Endpoint: /user/refresh
@user.route("/refresh", methods=["GET", "POST"])
@jwt_required(refresh=True)
def refresh():
    """Endpoint to refresh the user's access token."""

    user = get_current_user()

    access_token = generate_access_token(user)
    db.session.commit()

    response = jsonify({"access_token": access_token})
    set_access_cookies(response, access_token)

    return (response, HTTPStatus.OK)


# Endpoint: /user
@user.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_user():
    user = get_current_user()
    if user:
        return jsonify(user.to_dict(simplified=False)), HTTPStatus.OK

    return jsonify(None), HTTPStatus.NOT_FOUND


# Endpoint: /user/login
@user.route("/login", methods=["POST"])
@use_args({"email": fields.Email(required=True), "password": fields.Str(required=True)})
def login(args):
    # Get the user corresponding to the email that is logging in
    user = db.session.query(User).filter_by(email=args["email"], is_mock=False).first()

    # Check if user exists and if the given password is correct
    if not user or not user.check_password(args["password"]):
        return error_response(
            "Incorrect email or password", ErrorType.INCORRECT_CREDENTIALS
        )

    # # Check it the user has the email verified
    # if user.mail_is_verified is False:
    #     return error_response("Email not verified", ErrorType.USER_NOT_VERIFIED)

    # # Check it the user has the phone number verified
    # if user.phone_is_verified is False:
    #     return error_response("Phone not verified", ErrorType.USER_NOT_VERIFIED)

    # Generate and commit the access token for the user
    access_token = generate_access_token(user)
    db.session.commit()

    if user.auth_level in [
        AuthLevelEnum.SCHOOL_ADMIN,
        AuthLevelEnum.SUPER_ADMIN,
    ]:
        # Nothing for now
        pass

    response = jsonify(
        {"access_token": access_token, "user": user.to_dict(simplified=True)}
    )

    set_access_cookies(response, access_token)
    set_refresh_cookies(
        response,
        generate_refresh_token(user),
        max_age=current_app.config["JWT_REFRESH_TOKEN_EXPIRES"],
    )

    return (response, HTTPStatus.OK)


# Endpoint: /user/new
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
    }
)
def new_user(args):
    """Endpoint to create a new user."""
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

    if "language" in args and args["language"]:
        language = args["language"]
    else:
        language = SupportedLanguagesEnum.ENGLISH

    if language not in SupportedLanguagesEnum.values():
        return error_response(
            f"Invalid language: {language} is not one of {' '.join(SupportedLanguagesEnum.values())}",
            ErrorType.BAD_REQUEST,
        )

    if "school" in args and args["school"]:
        school = db.session.query(School).filter_by(name=args["school"]).first()
    else:
        school = db.session.query(School).filter_by(name="Cornell University").first()

    if not school:
        return error_response("Invalid school.", ErrorType.BAD_REQUEST)

    major = (
        db.session.query(Major)
        .filter_by(name=args["major"], school_id=school.id)
        .first()
    )

    if not major:
        return error_response("Invalid Major.", ErrorType.BAD_REQUEST)

    # Hash password  before storing it in the db for privacy purposes
    hashed_password = User.hash_password(args["password"])

    # New Username (funny)
    n = 3
    counter = 0
    username = generate_funny_username(n)
    while db.session.query(User).filter_by(username=username).first():
        # print(username)
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

    # Generate and commit the access token for the user
    access_token = generate_access_token(user)
    db.session.commit()

    response = jsonify(
        {"access_token": access_token, "user": user.to_dict(simplified=True)}
    )

    set_access_cookies(response, access_token)
    set_refresh_cookies(
        response,
        generate_refresh_token(user),
        max_age=current_app.config["JWT_REFRESH_TOKEN_EXPIRES"],
    )

    return (response, HTTPStatus.CREATED)
