# Local Application imports
from edify import create_app
from edify.config import Config
from edify.models import *
from edify.utils.constants import EdifyEnvironments
from socketio_ext import socketio
from flask_socketio import join_room

# Create the Flask app
app = create_app(Config)

socketio.init_app(app)


@socketio.on("join")
def on_join(data):
    """
    Handle users joining their unique WebSocket room.
    `data` is expected to contain the user's ID.
    """
    user_id = data.get("user_id")
    if user_id:
        room_name = f"user_{user_id}"  # Create a unique room for the user
        join_room(room_name)
        print(f"User {user_id} joined room: {room_name}")
    else:
        print("Error: Missing user_id in 'join' event data.")


# Run the Flask app
if __name__ == "__main__":
    print("Running on production...\n")

    if app.config["ENV"] == EdifyEnvironments.LOCAL.value:
        print("Running locally...\n")
        app.run(debug=False)

    elif app.config["ENV"] == EdifyEnvironments.TEST.value:
        print("Running tests...\n")
        app.run(debug=True)

    else:
        print("Invalid environment.")
