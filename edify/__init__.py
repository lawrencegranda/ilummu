# Standard Library imports
from http import HTTPStatus
import traceback

# Third-Party Framework imports
import boto3
from flask import Flask, request, jsonify, session, url_for, redirect, current_app
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    get_jwt_identity,
    verify_jwt_in_request,
    set_access_cookies,
)
from flask_jwt_extended.exceptions import (
    UserLookupError,
    NoAuthorizationError,
    JWTExtendedException,
)
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.exceptions import HTTPException
from jwt.exceptions import ExpiredSignatureError, PyJWTError

# Local Application imports
from edify.utils.utils import (
    internal_request,
    get_request_cookie,
    get_access_header,
    handle_invalid_token,
)

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
migrate = Migrate()
mail = Mail()
s3_client = None


def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize S3 client only if not in testing mode
    if not config_class.TESTING:
        global s3_client
        s3_client = boto3.client(
            "s3",
            endpoint_url=app.config["FILEBASE_ENDPOINT"],
            aws_access_key_id=app.config["FILEBASE_ACCESS_KEY"],
            aws_secret_access_key=app.config["FILEBASE_SECRET_KEY"],
        )

    # Passing app as a parameter here instead of on initialization
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    mail.state = mail.init_app(
        app
    )  # Had to do this because there is an error in source code.

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
        print(f"ERROR: User not found: {e}")
        return handle_invalid_token()

    @frontend.errorhandler(ExpiredSignatureError)
    @frontend.errorhandler(NoAuthorizationError)
    def expired_jwt(e):
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

    app.register_blueprint(frontend)
    app.register_blueprint(backend)

    print("\n------ URL MAP: ------\n", app.url_map, "\n----------------------\n")

    return app
