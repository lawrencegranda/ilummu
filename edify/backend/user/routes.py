"""User-related routes and authentication endpoints for the Edify backend."""

# Standard Library imports
from datetime import datetime
from http import HTTPStatus

# Third-Party Framework imports
from flask import Blueprint, url_for, jsonify, current_app, render_template
from flask.typing import ResponseReturnValue
from flask_jwt_extended import (
    jwt_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from webargs import fields, validate
from webargs.flaskparser import use_args

# Local Application imports
from edify.core import db
from edify.models import User
from edify.utils.constants import (
    ErrorType,
    AuthLevelEnum,
    NotificationTypeEnum,
)
from edify.utils.utils import (
    error_response,
    validate_password,
)
from edify.backend.user.utils import (
    get_current_user,
    generate_refresh_token,
    validate_signup_data,
    make_login_response,
    create_new_user,
    prepare_user_args,
)
from edify.backend.mail.utils import send
from edify.backend.utils import commit_changes, create_notification

# -----------------------------------------------------------------------------
# Route Blueprint
# -----------------------------------------------------------------------------
# Endpoint: /backend/user/
user = Blueprint("user", __name__, url_prefix="/user")


# -----------------------------------------------------------------------------
# Blueprint Endpoints (user)
# -----------------------------------------------------------------------------


# Endpoint: /backend/user
@user.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_user() -> ResponseReturnValue:
    """
    Endpoint to get the current user's information.

    Returns:
        Response: JSON response with the user's information or None if not found.
    """
    try:
        curr_user = get_current_user()
        if curr_user:
            return (
                jsonify({"user": curr_user.to_dict(simplified=False)}),
                HTTPStatus.OK,
            )
    except (ValueError, KeyError, RuntimeError) as e:
        print(f"ERROR: Cannot get current user: {e}")

    return jsonify(None), HTTPStatus.NOT_FOUND


# Endpoint: /backend/user/is_verified
@user.route("/is_verified", methods=["GET"])
@jwt_required(optional=True)
def is_verified() -> ResponseReturnValue:
    """
    Endpoint to check whether the current user is verified.

    Returns:
        Response: true or false.
    """
    curr_user = get_current_user()
    if curr_user and (curr_user.mail_is_verified or curr_user.phone_is_verified):
        return jsonify(True), HTTPStatus.OK

    return jsonify(False), HTTPStatus.OK


# TOKENS            %------------------------------------------------------------------%


# Endpoint: /backend/user/logout
@user.route("/logout", methods=["POST"])
def logout() -> ResponseReturnValue:
    """
    Endpoint to log out a curr_user.

    Returns:
        Response: JSON response indicating successful logout.
    """
    response = jsonify({"message": "Successfully logged out."})
    unset_jwt_cookies(response)
    return (response, HTTPStatus.OK)


# Endpoint: /backend/user/refresh
@user.route("/refresh", methods=["GET", "POST"])
@jwt_required(refresh=True)
def refresh() -> ResponseReturnValue:
    """
    Endpoint to refresh the user's access token.

    Returns:
        Response: JSON response with the new access token.
    """
    curr_user = get_current_user()
    print(f"JWT: Refreshing token... User {curr_user.id}")
    return make_login_response(curr_user, False), HTTPStatus.OK


# Endpoint: /backend/user/login
@user.route("/login", methods=["POST"])
@use_args(
    {
        "email": fields.Email(required=True),
        "password": fields.Str(required=True),
        "remember": fields.Boolean(required=False),
    },
    location="json",
)
def login(args: dict) -> ResponseReturnValue:
    """
    Endpoint to log in a user. Redirect Google users to Google OAuth if they attempt manual login.

    Args:
        args (dict): The login arguments containing email, password, and remember flag.

    Returns:
        Response: JSON response with the access token and user information or redirection error.
    """
    curr_user = (
        db.session.query(User).filter_by(email=args["email"], is_mock=False).first()
    )

    # If user not found, return error
    if not curr_user:
        return error_response(
            "Invalid email or password", ErrorType.INCORRECT_CREDENTIALS
        )

    # Prevent Google accounts from logging in with a password
    if curr_user.is_google_account:
        return (
            jsonify(
                {
                    "msg": "This account was created using Google. Please log in using Google.",
                    "type": "UNAUTHORIZED",
                    "redirect_to": url_for("oauth.login"),
                }
            ),
            ErrorType.INCORRECT_CREDENTIALS.value,
        )

    # Check if the provided password matches the stored password for the user.
    if not curr_user.check_password(args["password"]):
        return error_response(
            "Invalid email or password", ErrorType.INCORRECT_CREDENTIALS
        )

    # # Uncomment these lines to enable email and phone verification checks
    if curr_user.mail_is_verified is False:
        # return error_response("Email not verified", ErrorType.USER_NOT_VERIFIED)
        pass
    if curr_user.phone_is_verified is False:
        # return error_response("Phone not verified", ErrorType.USER_NOT_VERIFIED)
        pass

    if curr_user.auth_level in [AuthLevelEnum.SCHOOL_ADMIN, AuthLevelEnum.SUPER_ADMIN]:
        # Additional logic for admin users (if needed)
        pass

    return make_login_response(curr_user, args.get("remember", False)), HTTPStatus.OK


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
def signup(args: dict) -> ResponseReturnValue:
    """Create a new user account."""
    # Validate input data
    if error := validate_signup_data(args):
        return error

    # Prepare and create user
    user_args = prepare_user_args(args)
    user_obj, error = create_new_user(**user_args)

    if error:
        return error

    return (
        make_login_response(user_obj, args.get("remember", False)),
        HTTPStatus.CREATED,
    )


# RESET EMAIL       %------------------------------------------------------------------%


# Endpoint: /backend/user/reset-email
@user.route("/reset-email", methods=["POST"])
@use_args(
    {
        "email": fields.Email(required=True),
    }
)
def reset_email(args: dict) -> ResponseReturnValue:
    """
    Endpoint to reset send an email to reset password.

    Args:
        args (dict): The login arguments containing email.

    Returns:
        Response: Send email.
    """
    # Get the user corresponding to the email that is logging in
    curr_user = (
        db.session.query(User)
        .filter_by(email=args["email"].lower(), is_mock=False)
        .first()
    )

    # If user not found, do not send email.
    if not curr_user:
        return jsonify({}), HTTPStatus.OK

    # Generate token.
    token = curr_user.generate_reset_token()

    # Format url with token
    url = url_for("frontend.reset_password", token=token, _external=True)

    # Render html
    html = render_template(
        "/reset_email.jinja", name=curr_user.username, action_url=url
    )

    # Send email
    send(
        subject="ilummu: Password reset request",
        html=html,
        recipients=[curr_user.email],
    )

    # Create a notification for the forgot password
    create_notification(
        NotificationTypeEnum.PASSWORD_RESET,
        (
            f"You initated the password reset process on "
            f'{datetime.now().strftime("%m/%d/%Y %H:%M")}.'
        ),
        user_id=curr_user.id,
        question_id=None,
    )

    return jsonify({}), HTTPStatus.OK


# Endpoint: /backend/user/check-reset-token
@user.route("/check-reset-token", methods=["GET"])
@use_args(
    {
        "token": fields.Str(required=True),
    },
    location="query",
)
def check_token(args: dict) -> ResponseReturnValue:
    """
    Endpoint to check a reset token.

    Args:
        args (dict): The token.

    Returns:
        Response: Tuple. Success or failure.
    """
    token = args["token"]
    curr_user = User.validate_reset_token(token)

    # Check if user exists
    if not curr_user:
        return error_response(
            "Invalid or expired reset link. Please try again.", ErrorType.BAD_REQUEST
        )

    return jsonify({}), HTTPStatus.OK


# Endpoint: /backend/user/reset-password
@user.route("/reset-password", methods=["POST"])
@use_args(
    {
        "password": fields.Str(required=True),
        "token": fields.Str(required=True),
    }
)
def reset_password(args: dict) -> ResponseReturnValue:
    """
    Endpoint to reset a password.

    Args:
        args (dict): The new password and the token.

    Returns:
        Response: Tuple. Access token and user, and code.
    """
    token = args["token"]
    curr_user = User.validate_reset_token(token)

    # Check if user exists
    if not curr_user:
        return error_response(
            "Invalid or expired reset link. Please try again.", ErrorType.BAD_REQUEST
        )

    password = args["password"]

    # Make sure it is a new password
    if curr_user.check_password(password):
        return error_response(
            "Password must be different from your last password.", ErrorType.BAD_REQUEST
        )

    # Check password
    valid, msg = validate_password(password)

    if not valid:
        return error_response(msg, ErrorType.BAD_REQUEST)

    # Hash password before storing it in the db for privacy purposes
    curr_user.password = User.hash_password(password)
    curr_user.password_last_reset = datetime.utcnow()
    commit_changes("Failed to reset password")

    # Create a notification for the password reset
    create_notification(
        NotificationTypeEnum.PASSWORD_RESET,
        f'Your password was reset on {datetime.now().strftime("%m/%d/%Y %H:%M")}.',
        user_id=curr_user.id,
        question_id=None,
    )

    # Generate the access token for the user
    access_token = curr_user.get_access_token()

    # Return access token and user
    response = jsonify(
        {"access_token": access_token, "user": curr_user.to_dict(simplified=True)}
    )

    # Set up cookies
    set_access_cookies(response, access_token)
    set_refresh_cookies(
        response,
        generate_refresh_token(curr_user),
        max_age=current_app.config["JWT_REFRESH_TOKEN_EXPIRES"],
    )

    return response, HTTPStatus.OK


# VERIFY EMAIL      %------------------------------------------------------------------%


# Endpoint: /backend/user/verify-email
@user.route("/verify-email", methods=["POST"])
@jwt_required()
def verify_email() -> ResponseReturnValue:
    """
    Endpoint to reset send an email to verify email.

    Args:
        args (dict): The login arguments containing email.

    Returns:
        Response: Send email.
    """
    curr_user = get_current_user()

    # If user not found, error
    if not curr_user:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    # If there is a valid code, sent recently, do not send
    if (
        curr_user.has_valid_session_auth_code()
        and curr_user.sec_since_issued_auth_code() < 50
    ):
        return (
            jsonify({"msg": "Email was already sent before and is still valid."}),
            HTTPStatus.OK,
        )

    # Generate code
    code = curr_user.generate_session_auth_code()

    # Render html
    html = render_template("/verify_email.jinja", name=curr_user.username, code=code)

    # Send email
    send(subject="ilummu: Verify your email", html=html, recipients=[curr_user.email])

    # Create a notification for the email sent
    create_notification(
        NotificationTypeEnum.PASSWORD_RESET,
        "A verification code was sent to your email!",
        user_id=curr_user.id,
        question_id=None,
    )

    return jsonify({}), HTTPStatus.OK


# Endpoint: /backend/user/check-auth-code
@user.route("/check-auth-code", methods=["POST"])
@jwt_required()
@use_args(
    {
        "code": fields.Int(required=True, validate=validate.Range(min=1)),
    },
    location="query",
)
def check_auth_code(args: dict) -> ResponseReturnValue:
    """
    Endpoint to check an identity verification auth token.

    Args:
        args (dict): The code.

    Returns:
        Response: Tuple. Success or failure.
    """
    code = args["code"]
    curr_user = get_current_user()

    # If user not found, error.
    if not curr_user:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    if not curr_user.validate_session_auth_code(code):
        return error_response("Invalid or expired code", ErrorType.BAD_REQUEST)

    # Set verified status
    curr_user.mail_is_verified = True
    commit_changes("Failed to verify email")

    # Create a notification for account verification
    create_notification(
        NotificationTypeEnum.ACCOUNT_VERIFIED,
        "Your email was verified successfully!",
        user_id=curr_user.id,
        question_id=None,
    )

    return jsonify({}), HTTPStatus.OK
