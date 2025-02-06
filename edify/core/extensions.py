"""Flask extensions initialization and configuration."""

# Third-Party Framework imports
import boto3
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail

# Initialize extensions
bcrypt = Bcrypt()
jwt = JWTManager()
mail = Mail()


def init_extensions(app):
    """Initialize Flask extensions."""
    # Initialize S3 client for file storage
    if not app.config["TESTING"]:
        app.config["S3_CLIENT"] = boto3.client(
            "s3",
            endpoint_url=app.config["FILEBASE_ENDPOINT"],
            aws_access_key_id=app.config["FILEBASE_ACCESS_KEY"],
            aws_secret_access_key=app.config["FILEBASE_SECRET_KEY"],
        )
    else:
        app.config["S3_CLIENT"] = None

    # Initialize extensions
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.state = mail.init_app(app)  # Fix for mail error in source code
