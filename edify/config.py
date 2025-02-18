"""Configuration for the Edify application."""

# Standard Library imports
from datetime import timedelta
import os

# Local Application imports
from edify.utils.constants import EdifyEnvironments
from edify.core.security.csp_config import get_csp_policy, generate_csp_header

# pylint: disable=too-few-public-methods
class Config:
    """Configuration for the Edify application."""

    MAINTENANCE_MODE = int(os.environ["MAINTENANCE_MODE"]) == 1

    SECRET_KEY = os.environ["SECRET_KEY"]
    JWT_SECRET_KEY = SECRET_KEY

    if not any(member.name == os.environ["ENV"] for member in EdifyEnvironments):
        raise EnvironmentError(f"Invalid Environment {os.environ['ENV']}")

    ENV = os.environ["ENV"]

    PROD = ENV == EdifyEnvironments.PRODUCTION.value
    LOCAL = ENV == EdifyEnvironments.LOCAL.value
    TESTING = ENV == EdifyEnvironments.TEST.value

    if PROD:
        SQLALCHEMY_DATABASE_URI = os.environ["DB_URL"]

        # Web settings
        HOST = os.environ["HOST"]
        PORT = os.environ["PORT"]

        GOOGLE_REDIRECT_URI = "https://"+HOST+":"+PORT+os.environ["GOOGLE_REDIRECT_URI"]

    elif LOCAL:
        SQLALCHEMY_DATABASE_URI = os.environ["DB_URL"]
        GOOGLE_REDIRECT_URI = "http://127.0.0.1:5000"+os.environ["GOOGLE_REDIRECT_URI"]

    elif TESTING:
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        GOOGLE_REDIRECT_URI = "http://127.0.0.1:5000"+os.environ["GOOGLE_REDIRECT_URI"]

    # Configure all the ways you want to allow JWTs to be sent.
    JWT_TOKEN_LOCATION = ["headers", "cookies"]

    # If true this will only allow the cookies that contain your JWTs to be sent
    # over https. In production, this should always be set to True.
    JWT_COOKIE_SECURE = True

    # Disable CSRF protection. In almost every case, this is a bad idea.
    # See examples/csrf_protection_with_cookies.py for how safely store JWTs
    # in cookies.
    JWT_COOKIE_CSRF_PROTECT = False

    # Controls if the cookies will be set as session cookies, which are deleted
    # when the browser is closed.
    JWT_SESSION_COOKIE = True

    # Control expiration time in seconds
    JWT_REFRESH_TOKEN_EXPIRES: int = int(timedelta(days=90).total_seconds())

    # Cookies should only be sent with requests from the same site, providing maximum
    # CSRF protection.
    JWT_COOKIE_SAMESITE = "Strict"

    # Mail config
    MAIL_SENDER = os.environ["MAIL_SENDER"]
    MAIL_USERNAME = os.environ["MAIL_USERNAME"]
    MAIL_PASSWORD = os.environ["MAIL_PASSWORD"]
    MAIL_SERVER = os.environ["MAIL_SERVER"]
    MAIL_PORT = os.environ["MAIL_PORT"]
    MAIL_USE_TLS = int(os.environ["MAIL_USE_TLS"]) == 1
    MAIL_USE_SSL = int(os.environ["MAIL_USE_SSL"]) == 1

    # Reset password time
    RESET_PASS_TOKEN_MAX_AGE: int = int(timedelta(minutes=10).total_seconds())

    # Auth token time
    AUTH_TOKEN_MAX_AGE: int = int(timedelta(minutes=30).total_seconds())

    # Filebase credentials
    FILEBASE_ACCESS_KEY: str = os.environ["FILEBASE_ACCESS_KEY"]
    FILEBASE_SECRET_KEY: str = os.environ["FILEBASE_SECRET_KEY"]
    FILEBASE_BUCKET: str = os.environ["FILEBASE_BUCKET"]
    FILEBASE_ENDPOINT: str = os.environ["FILEBASE_ENDPOINT"]
    FILEBASE_URL: str = os.environ["FILEBASE_URL"]

    # Google OAuth2 Config
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False  # Session is not permanent

    GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]

    GOOGLE_REDIRECT_URI = os.environ["GOOGLE_REDIRECT_URI"]

    # CSP Policy (imported from security config)
    CSP_POLICY = get_csp_policy(FILEBASE_URL)
    CSP_HEADER = generate_csp_header(CSP_POLICY)
