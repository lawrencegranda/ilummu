from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate


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
    # This is so that the extension object does not initialy get bound to the application.
    # Using this design pattern, no application specific state is stored on the extension
    # object so one extension object can be used for multiple apps.
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    from edify.routes.routes import frontend, question

    app.register_blueprint(frontend)
    app.register_blueprint(question)

    # Return validation errors as JSON
    @app.errorhandler(422)
    def handle_error(err):
        headers = err.data.get("headers", None)
        messages = err.data.get("messages", ["Invalid request."])
        if headers:
            return jsonify({"errors": messages}), err.code, headers
        else:
            return jsonify({"errors": messages}), err.code

    print("\n------ URL MAP: ------\n", app.url_map, "\n----------------------\n")

    return app
