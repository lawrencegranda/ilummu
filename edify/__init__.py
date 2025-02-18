"""Flask application factory and configuration for the Edify platform."""

# Standard Library imports
from http import HTTPStatus

# Third-Party Framework imports
from flask import Flask, request, url_for, redirect
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    verify_jwt_in_request,
    set_access_cookies,
)

# Local Application imports
from edify.core import init_db, init_extensions
from edify.core.error_handlers import register_error_handlers
from edify.utils.utils import internal_request, get_access_header


def create_app(config_class):
    """Flask application factory function."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize core components
    init_db(app)
    init_extensions(app)

    # pylint: disable=import-outside-toplevel
    from edify.frontend.routes import frontend
    from edify.backend.routes import backend
    from edify.backend.oauth.routes import oauth

    # pylint: enable=all

    # -----------------------------------------------------------------------------
    # Security
    # -----------------------------------------------------------------------------

    @frontend.before_request
    def enforce_https():
        """Redirect to HTTPS if not already using it."""
        if (
            config_class.PROD
            and not request.is_secure
            and request.headers.get("X-Forwarded-Proto", "http") != "https"
        ):
            url = request.url.replace("http://", "https://", 1)
            return redirect(url, code=301)
        return None

    @frontend.after_request
    def add_csp_header(response):
        """
        Add CSP Headers
        """
        if config_class.PROD:
            response.headers["Content-Security-Policy"] = config_class.CSP_HEADER

        return response

    # -----------------------------------------------------------------------------
    # Cookies
    # -----------------------------------------------------------------------------

    @frontend.before_request
    @jwt_required(optional=True, refresh=True)
    def before_request_func():
        user_id = get_jwt_identity()

        if user_id and (
            "access_token_cookie" not in request.cookies
            or not verify_jwt_in_request(optional=True)
        ):
            refresh = internal_request(url_for("backend.user.refresh"))

            # Parse the response
            data, status = refresh.get_json(), refresh.status_code

            if status == HTTPStatus.OK:
                # Modify the request headers to include the new access token
                request.environ["HTTP_AUTHORIZATION"] = (
                    f'Bearer {data["access_token"].strip()}'
                )

    @frontend.after_request
    def after_request_func(response):
        token = get_access_header(request)
        if token:
            # Modify the response to include the new access token cookie
            set_access_cookies(
                response,
                token,
            )

        return response

    # -----------------------------------------------------------------------------
    # Register Error Handlers
    # -----------------------------------------------------------------------------
    register_error_handlers(frontend, oauth)

    # -----------------------------------------------------------------------------
    # Blueprints
    # -----------------------------------------------------------------------------

    app.register_blueprint(frontend)
    app.register_blueprint(backend)
    app.register_blueprint(oauth)

    print("\n------ URL MAP: ------\n", app.url_map, "\n----------------------\n")

    return app
