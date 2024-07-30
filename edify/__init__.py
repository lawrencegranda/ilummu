from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    unset_jwt_cookies,
    jwt_required,
    verify_jwt_in_request,
)
from flask_jwt_extended.exceptions import UserLookupError
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException
from http import HTTPStatus
from jwt.exceptions import ExpiredSignatureError

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
        token = verify_jwt_in_request(optional=True, refresh=True)

        if not token:
            return redirect(url_for("frontend.logout"))

        print(token)

        return e

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
