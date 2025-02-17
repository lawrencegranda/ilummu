"""
This script is used to run the Flask app.
"""

# Local Application imports
from edify import create_app
from edify.config import Config
from edify.core import socketio

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from edify.models import *
from edify.utils.constants import EdifyEnvironments

# pylint: enable=all

# Create the Flask app
app = create_app(Config)

# Run the Flask app
if __name__ == "__main__":
    print("Running on production...\n")

    if app.config["ENV"] == EdifyEnvironments.LOCAL.value:
        print("Running locally...\n")
        socketio.run(
            app,
            host="127.0.0.1",
            port=5000,
            debug=False,
            use_reloader=False,
            log_output=True,
        )

    elif app.config["ENV"] == EdifyEnvironments.TEST.value:
        print("Running tests...\n")
        socketio.run(
            app,
            host="127.0.0.1",
            port=5000,
            debug=True,
            use_reloader=False,
            log_output=True,
        )

    else:
        print("Invalid environment.")
