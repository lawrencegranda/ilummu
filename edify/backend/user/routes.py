from flask import Blueprint, url_for, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    decode_token,
    jwt_required,
    current_user,
)
from webargs import fields, validate
from webargs.flaskparser import use_args
import os
import json
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
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
from edify import db
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
from edify import db, bcrypt
from http import HTTPStatus

user = Blueprint("user", __name__, url_prefix="/user")


def generate_access_token(user, days=5):
    access_token = create_access_token(
        identity=user.id, expires_delta=timedelta(days=days)
    )
    user.token = access_token
    user.token_last_refresh = datetime.utcnow()
    return access_token


# Endpoint: user/login
@user.route("/login", methods=["POST"])
@use_args({"email": fields.Email(required=True), "password": fields.Str(required=True)})
def login(args):
    # Get the user corresponding to the email that is logging in
    user = db.session.query(User).filter_by(email=args["email"], is_mock=False).first()

    # Check if user exists and if the given password is correct
    if not user or not bcrypt.check_password_hash(user.password, args["password"]):
        return error_response(
            "Incorrect email or password", ErrorType.INCORRECT_CREDENTIALS
        )

    # # Check it the user has the email verified
    # if user.mail_is_verified is False:
    #     return error_response("Email not verified", ErrorType.USER_NOT_VERIFIED)

    # # Check it the user has the phone number verified
    # if user.phone_is_verified is False:
    #     return error_response("Phone not verified", ErrorType.USER_NOT_VERIFIED)

    # Authentication token to be used in subsequent requests
    access_token = create_access_token(
        identity=user.id, expires_delta=timedelta(days=5)
    )

    # Generate and commit the access token for the user for 5 days
    generate_access_token(user, 5)
    db.session.commit()

    if user.auth_level in [
        AuthLevelEnum.SCHOOL_ADMIN,
        AuthLevelEnum.SUPER_ADMIN,
    ]:
        # Nothing for now
        pass

    return (
        jsonify({"token": access_token, "user": user.to_dict(simplified=True)}),
        HTTPStatus.OK,
    )


# Endpoint: user/new
@user.route("/new", methods=["POST"])
@use_args(
    {
        "firstname": fields.Str(required=True, validate=validate.Length(min=2, max=20)),
        "lastname": fields.Str(required=True, validate=validate.Length(min=2, max=35)),
        "email": fields.Email(required=True, validate=validate.Length(min=3, max=120)),
        "phone": fields.Str(required=True, validate=validate.Length(min=12, max=19)),
        "password": fields.Str(required=True),
        "school": fields.Str(required=True),
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

    language = args["language"]
    if not language:
        language = SupportedLanguagesEnum.ENGLISH

    if language not in SupportedLanguagesEnum.values():
        return error_response(
            f"Invalid language: {language} is not one of {' '.join(SupportedLanguagesEnum.values())}",
            ErrorType.BAD_REQUEST,
        )

    if args["school"]:
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
    hashed_password = bcrypt.generate_password_hash(args["password"]).decode("utf-8")

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

    # Generate and commit the access token for the user for 5 days
    access_token = generate_access_token(user, 5)
    db.session.commit()

    return (
        jsonify({"token": access_token, "user": user.to_dict(simplified=True)}),
        HTTPStatus.CREATED,
    )
