"""Flask extensions initialization and configuration."""

# Third-Party Framework imports
import boto3
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_socketio import SocketIO, join_room

# Initialize extensions
bcrypt = Bcrypt()
jwt = JWTManager()
mail = Mail()
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")


@socketio.on("join")
def on_join(data):
    """
    Handle users joining their unique WebSocket room.
    `data` is expected to contain the user's ID.
    """
    user_id = data.get("user_id")
    if user_id:
        room_name = f"user_{user_id}"  # unique user id
        join_room(room_name)
        print(f"User {user_id} joined room: {room_name}")
    else:
        print("ERROR: SocketIO. Missing user_id in 'join' event data.")


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
    socketio.init_app(app)
