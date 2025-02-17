"""OAuth Routes for Google Authentication."""

# Standard Library imports
from http import HTTPStatus
import os

# Third-Party Framework imports
from flask import (
    Blueprint,
    url_for,
    jsonify,
    current_app,
    request,
    redirect,
    session,
    render_template,
)
from flask import typing as flask_typing
from flask_jwt_extended import (
    set_access_cookies,
    set_refresh_cookies,
)
from webargs import fields
from webargs.flaskparser import use_args
from webargs import validate
from requests_oauthlib import OAuth2Session

# Local Application imports
from edify.core import db
from edify.models import User, School, Major
from edify.utils.constants import SupportedLanguagesEnum
from edify.utils.utils import (
    validate_phone,
    format_phone,
    generate_funny_username,
)
from edify.backend.user.utils import generate_refresh_token

# Allow HTTP for local development (testing only)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# -----------------------------------------------------------------------------
# Blueprint Definition
# -----------------------------------------------------------------------------
oauth = Blueprint("oauth", __name__)


# -----------------------------------------------------------------------------
# OAuth Setup
# -----------------------------------------------------------------------------
@oauth.before_app_first_request
def setup_oauth():
    """Initialize the OAuth2 session."""
    current_app.config["OAUTH_SESSION"] = OAuth2Session(
        client_id=current_app.config["GOOGLE_CLIENT_ID"],
        redirect_uri=current_app.config["GOOGLE_REDIRECT_URI"],
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
    )
    current_app.logger.info("OAuth2 session configured successfully.")


def get_oauth_session():
    """Retrieve the OAuth session from Flask's app context."""
    return current_app.config.get("OAUTH_SESSION")


# -----------------------------------------------------------------------------
# OAuth Routes
# -----------------------------------------------------------------------------
@oauth.route("/login/google")
def login() -> flask_typing.ResponseReturnValue:
    """Redirect the user to Google's OAuth 2.0 authorization page."""
    oauth_session = get_oauth_session()
    try:
        authorization_url, state = oauth_session.authorization_url(
            "https://accounts.google.com/o/oauth2/auth",
            access_type="offline",
            prompt="select_account",
        )
        session["oauth_state"] = state
        return redirect(authorization_url)
    except KeyError as e:
        current_app.logger.error(
            f"KeyError during Google authorization URL generation: {e}"
        )
        return (
            jsonify({"error": "A required parameter is missing. Please try again."}),
            HTTPStatus.BAD_REQUEST,
        )
    except ConnectionError as e:
        current_app.logger.error(f"ConnectionError during Google authorization: {e}")
        return (
            jsonify(
                {
                    "error": "Failed to connect to Google. Please check your network and try again."
                }
            ),
            HTTPStatus.SERVICE_UNAVAILABLE,
        )


@oauth.route("/login/google/callback")
def callback() -> flask_typing.ResponseReturnValue:
    """
    Handle the callback from Google OAuth.
    """
    oauth_session = get_oauth_session()
    try:
        if request.args.get("state") != session.get("oauth_state"):
            current_app.logger.error("State mismatch detected.")
            return redirect(url_for("frontend.signup"))

        # Exchange authorization code for token and fetch user info
        oauth_session.fetch_token(
            "https://oauth2.googleapis.com/token",
            authorization_response=request.url,
            client_secret=current_app.config["GOOGLE_CLIENT_SECRET"],
        )
        user_info = oauth_session.get("https://www.googleapis.com/oauth2/v1/userinfo").json()

        # Check if the user already exists
        user = db.session.query(User).filter_by(email=user_info["email"]).first()

        if user:
            # Generate tokens for existing user and refresh page
            access_token = user.get_access_token()
            refresh_token = generate_refresh_token(user)

            response = redirect(url_for("frontend.dashboard"))
            set_access_cookies(response, access_token)
            set_refresh_cookies(response, refresh_token)
            return response

        # Store user info in session to complete signup later
        session["user"] = user_info
        return redirect(url_for("oauth.google_signup_form"))

    except Exception as e:
        current_app.logger.error(f"Error during OAuth callback: {e}")
        return redirect(url_for("frontend.signup"))


@oauth.route("/signup/form", methods=["GET"])
def google_signup_form() -> flask_typing.ResponseReturnValue:
    """Render signup form for users authenticated with Google but do not have an account yet."""
    user_info = session.get("user")
    if not user_info:
        return redirect(url_for("frontend.signup"))

    # Check if user exists (shouldn't reach here)
    user = db.session.query(User).filter_by(email=user_info["email"]).first()
    if user:
        access_token = user.get_access_token()
        refresh_token = generate_refresh_token(user)
        response = redirect(url_for("frontend.dashboard"))
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        return response

    return render_template(
        "continue_google_signup.jinja",
        email=user_info.get("email"),
        firstname=user_info.get("given_name"),
        lastname=user_info.get("family_name"),
    )


@oauth.route("/signup", methods=["POST"])
@use_args(
    {
        "email": fields.Email(required=True),
        "firstname": fields.Str(required=True),
        "lastname": fields.Str(required=True),
        "phone": fields.Str(required=True, validate=validate.Length(min=10, max=15)),
        "major": fields.Str(required=True),
        "graduation": fields.Date(required=True),
        "language": fields.Str(missing=SupportedLanguagesEnum.ENGLISH),
    },
    location="json",
)
def google_signup(args) -> flask_typing.ResponseReturnValue:
    """Complete the Google OAuth-based signup process."""
    user = db.session.query(User).filter_by(email=args["email"]).first()
    if user:
        return redirect(url_for("frontend.login"))

    # Validate and format phone number
    phone = args["phone"]
    if not validate_phone(phone):
        return jsonify({"error": "Invalid phone format."}), HTTPStatus.BAD_REQUEST
    phone = format_phone(phone)

    # Get school and major information
    school = db.session.query(School).filter_by(name="Cornell University").first()
    major = (
        db.session.query(Major)
        .filter_by(name=args["major"], school_id=school.id)
        .first()
    )

    if not school or not major:
        return jsonify({"error": "Invalid school or major."}), HTTPStatus.BAD_REQUEST

    # Generate unique username
    username = generate_funny_username(3)
    while db.session.query(User).filter_by(username=username).first():
        username = generate_funny_username(4)

    # Create user
    user = User(
        username=username,
        firstname=args["firstname"],
        lastname=args["lastname"],
        email=args["email"],
        phone=phone,
        password=User.hash_password("google_oauth"),
        school_id=school.id,
        major_id=major.id,
        graduation=args["graduation"],
        language=args["language"],
        mail_is_verified=True,  # Automatically mark email as verified
    )

    db.session.add(user)
    db.session.commit()

    # Generate tokens and set cookies
    access_token = user.get_access_token()
    refresh_token = generate_refresh_token(user)

    response = redirect(url_for("frontend.dashboard"))
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)

    return response
