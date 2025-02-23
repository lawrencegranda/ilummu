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
    make_response,
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
    fetch_data,
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
def init_oauth(app):
    """
    Initialize the OAuth2 session.

    Args:
        app: The Flask application instance.
    """
    # Only set up OAuth if we're not in testing mode and not already configured
    if not app.config.get("TESTING") and "OAUTH_SESSION" not in app.config:
        app.config["OAUTH_SESSION"] = OAuth2Session(
            client_id=app.config["GOOGLE_CLIENT_ID"],
            redirect_uri=app.config["GOOGLE_REDIRECT_URI"],
            scope=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email",
            ],
        )
        app.logger.info("OAuth2 session configured successfully.")


def get_oauth_session():
    """
    Retrieve the OAuth session from Flask's app context.

    Returns:
        OAuth2Session: The OAuth2 session instance or None if in testing mode.
    """
    # Return None if we're in testing mode
    if current_app.config.get("TESTING"):
        return None
    return current_app.config.get("OAUTH_SESSION")


# Register init_oauth to be called when the blueprint is registered
oauth.record(lambda state: init_oauth(state.app))


# -----------------------------------------------------------------------------
# OAuth Routes
# -----------------------------------------------------------------------------


# Endpoint: /backend/oauth/login/google
@oauth.route("/login/google")
def login() -> flask_typing.ResponseReturnValue:
    """
    Redirect the user to Google's OAuth 2.0 authorization page.

    Returns:
        Response: A redirection to the Google authorization URL or an error response.
    """
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


# Endpoint: /backend/oauth/login/google/callback
@oauth.route("/login/google/callback")
def callback() -> flask_typing.ResponseReturnValue:
    """
    Handle Google OAuth callback.

    Returns:
        Response: A redirection to the appropriate URL based on the OAuth callback result.
    """
    oauth_session = get_oauth_session()
    redirect_url = url_for("frontend.signup")
    try:
        if request.args.get("state") != session.get("oauth_state"):
            current_app.logger.error("State mismatch detected.")
        else:
            oauth_session.fetch_token(
                "https://oauth2.googleapis.com/token",
                authorization_response=request.url,
                client_secret=current_app.config["GOOGLE_CLIENT_SECRET"],
            )
            user_info = oauth_session.get(
                "https://www.googleapis.com/oauth2/v1/userinfo"
            ).json()

            user = db.session.query(User).filter_by(email=user_info["email"]).first()

            if user:
                if not user.is_google_account:
                    return redirect(url_for("frontend.login", error="manual_account"))

                # Generate tokens and set cookies
                access_token = user.get_access_token()
                refresh_token = generate_refresh_token(user)

                # Instead of redirecting directly, render a template that will handle the auth state
                response = make_response(
                    render_template(
                        "auth_redirect.jinja",
                        redirect_url=url_for("frontend.dashboard"),
                    )
                )
                set_access_cookies(response, access_token)
                set_refresh_cookies(response, refresh_token)
                return response

            # Store user info in session for new signups
            session["user"] = user_info
            redirect_url = url_for("oauth.google_signup_form")

    except (KeyError, ConnectionError, ValueError, RuntimeError) as e:
        current_app.logger.error(f"Error during OAuth callback: {e}")

    return redirect(redirect_url)


def prepare_signup_form_data() -> dict:
    """
    Prepare data for rendering the signup form.

    Returns:
        dict: A dictionary containing majors, OAuth URL, next URL, and HTTP method.
    """
    majors = fetch_data(url_for("backend.data.fetch_user_majors"), "GET")
    majors.sort(key=lambda d: d["name"])

    return {
        "majors": majors,
        "oauth_url": url_for("backend.oauth.login", _external=True),
        "next_url": request.args.get("next_url", url_for("frontend.index")),
        "http_method": request.args.get("http_method", "GET"),
    }


# Endpoint: /backend/oauth/signup/form
@oauth.route("/signup/form", methods=["GET"])
def google_signup_form() -> flask_typing.ResponseReturnValue:
    """
    Render signup form for users authenticated with Google but do not have an account yet.

    Returns:
        Response: A redirection to the signup form or login page based on user info.
    """
    user_info = session.get("user")
    if not user_info:
        return redirect(url_for("frontend.signup"))

    # Check if email already exists in the database
    existing_user = db.session.query(User).filter_by(email=user_info["email"]).first()
    if existing_user:
        current_app.logger.info(
            f"Google Signup Attempt with Existing Email: {user_info['email']}"
        )
        return redirect(url_for("frontend.login"))

    form_data = prepare_signup_form_data()

    return render_template(
        "continue_google_signup.jinja",
        email=user_info.get("email"),
        firstname=user_info.get("given_name"),
        lastname=user_info.get("family_name"),
        majors=form_data["majors"],
        login=False,
        next_url=form_data["next_url"],
        http_method=form_data["http_method"],
        oauth_url=form_data["oauth_url"],
    )


# Endpoint: /backend/oauth/signup
@oauth.route("/signup", methods=["POST"])
@use_args(
    {
        "email": fields.Email(required=True),
        "firstname": fields.Str(required=True),
        "lastname": fields.Str(required=True),
        "phone": fields.Str(required=True, validate=validate.Length(min=10, max=15)),
        "major": fields.Str(required=True),
        "graduation": fields.Date(required=True),
        "language": fields.Str(load_default=SupportedLanguagesEnum.ENGLISH),
    },
    location="json",
)
def google_signup(args) -> flask_typing.ResponseReturnValue:
    """
    Prevent signing up with Google if email already exists for a manual login account.

    Args:
        args: The signup arguments containing email, firstname, lastname,
              phone, major, graduation, and language.

    Returns:
        Response: A redirection to the appropriate URL based on the signup result.
    """
    existing_user = db.session.query(User).filter_by(email=args["email"]).first()

    if existing_user and not existing_user.is_google_account:
        return redirect(url_for("frontend.login", error="manual_account"))

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

    # Create user with Google account flag
    user = User(
        username=username,
        firstname=args["firstname"],
        lastname=args["lastname"],
        email=args["email"],
        phone=phone,
        password=None,  # Google accounts have no manual password
        school_id=school.id,
        major_id=major.id,
        graduation=args["graduation"],
        language=args["language"],
        is_google_account=True,  # Mark as a Google account
        mail_is_verified=True,
    )

    db.session.add(user)
    db.session.commit()

    # Generate tokens and set cookies
    access_token = user.get_access_token()
    refresh_token = generate_refresh_token(user)

    # Instead of redirecting directly to dashboard
    response = make_response(
        render_template(
            "auth_redirect.jinja", redirect_url=url_for("frontend.dashboard")
        )
    )
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response
