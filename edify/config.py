"""Configuration for the Edify application."""

# Standard Library imports
from datetime import timedelta
import os

# Local Application imports
from edify.utils.constants import EdifyEnvironments


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

    elif LOCAL:
        SQLALCHEMY_DATABASE_URI = os.environ["DB_URL"]

    elif TESTING:
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

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

    # CSP Policy
    CSP_POLICY = {
        "default-src": "'self'",
        "script-src": [
            "'self'",
            "https://ajax.googleapis.com",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",
            "https://code.jquery.com",  # Add this to allow jQuery CDN
            "'unsafe-inline'",  # Use hashes or nonces in production
        ],
        "style-src": [
            "'self'",
            "https://maxcdn.bootstrapcdn.com",
            "https://fonts.googleapis.com",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",
            "'unsafe-inline'",  # Use hashes in production
        ],
        "font-src": [
            "'self'",
            "https://fonts.gstatic.com",
            "https://maxcdn.bootstrapcdn.com",
        ],
        "img-src": [
            "'self'",
            "data:",
            "https://cdnjs.cloudflare.com",  # Allow images from cdnjs.cloudflare.com
            "https://robohash.org",  # For the pictures
            FILEBASE_URL,  # Files
        ],
    }

    # Convert the CSP_POLICY dictionary to a string for the header
    CSP_HEADER = "; ".join(
        f"{key} {' '.join(value) if isinstance(value, list) else value}"
        for key, value in CSP_POLICY.items()
    )
