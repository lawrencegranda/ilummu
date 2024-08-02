# Standard Library imports
from http import HTTPStatus

# Third-Party Framework imports
from flask import Flask, request, jsonify, session, url_for, redirect, current_app
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    unset_jwt_cookies,
    unset_access_cookies,
    jwt_required,
    get_jwt_identity,
    verify_jwt_in_request,
    set_access_cookies,
)
from flask_jwt_extended.exceptions import UserLookupError
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException
from jwt.exceptions import ExpiredSignatureError

# Local Application imports
from edify.utils.utils import internal_request, get_request_cookie, get_access_header


# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
migrate = Migrate()


def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Passing app as a parameter here instead of on initialization
    # (FlaskDoc)
    # This is so that the extension object does not initially get bound to the application.
    # Using this design pattern, no application specific state is stored on the extension
    # object so one extension object can be used for multiple apps.
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    from edify.frontend.routes import frontend
    from edify.backend.routes import backend

    @frontend.before_request
    @jwt_required(optional=True, refresh=True)
    def before_request_func():
        id = get_jwt_identity()

        if id and (
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
    # Error Handlers
    # -----------------------------------------------------------------------------
    @frontend.errorhandler(UserLookupError)
    def invalid_user(e):
        # Possible fix: logout to unset cookies
        print(f"User not found: {e}")
        return redirect(url_for("frontend.logout"))

    @frontend.errorhandler(ExpiredSignatureError)
    def expired_jwt(e):
        response = redirect(url_for("frontend.logout"))
        unset_jwt_cookies(response)

        return response

    @frontend.errorhandler(Exception)
    def handle_error(e):
        print(f"{type(e)}: {e}")
        return (
            jsonify("An unexpected error occurred."),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    app.register_blueprint(frontend)
    app.register_blueprint(backend)

    print("\n------ URL MAP: ------\n", app.url_map, "\n----------------------\n")

    return app
