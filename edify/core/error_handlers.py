"""Error handlers for the Edify platform."""

# Standard Library imports
from http import HTTPStatus
import traceback

# Third-Party Framework imports
from flask import jsonify, current_app
from flask_jwt_extended.exceptions import (
    UserLookupError,
    NoAuthorizationError,
    JWTExtendedException,
)
from jwt.exceptions import ExpiredSignatureError, PyJWTError

# Local Application imports
from edify.utils.utils import handle_invalid_token


def register_error_handlers(frontend, oauth):
    """Register all error handlers for the application."""

    # -----------------------------------------------------------------------------
    # Frontend JWT Error Handlers
    # -----------------------------------------------------------------------------

    @frontend.errorhandler(UserLookupError)
    def invalid_user(e):
        print(f"ERROR: User not found: {e}")
        return handle_invalid_token()

    @frontend.errorhandler(ExpiredSignatureError)
    @frontend.errorhandler(NoAuthorizationError)
    def expired_jwt(_):
        return handle_invalid_token()

    @frontend.errorhandler(JWTExtendedException)
    @frontend.errorhandler(PyJWTError)
    def general_jwt(e):
        print(f"ERROR: General JWT exception: {e}")
        return handle_invalid_token()

    @frontend.errorhandler(Exception)
    def handle_error(e):
        print(f"ERROR: Uncaught error ({type(e)}): {e}")
        print(traceback.format_exc())
        return (
            jsonify("An unexpected error occurred."),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    # -----------------------------------------------------------------------------
    # OAuth Error Handlers
    # -----------------------------------------------------------------------------

    @oauth.errorhandler(Exception)
    def handle_general_oauth_error(e):
        current_app.logger.error(f"General OAuth exception: {e}")
        return (
            jsonify({"error": "An unexpected error occurred during OAuth processing."}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
