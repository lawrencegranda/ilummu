# Local Application imports
from edify import create_app
from edify.config import Config
from edify.models import *
from edify.utils.constants import EdifyEnvironments

# Create the Flask app
app = create_app(Config)

# Run the Flask app
if __name__ == "__main__":
    if app.config["ENV"] == EdifyEnvironments.PRODUCTION.value:
        print("Running on production...\n")
        app.run(host=app.config["HOST"], port=app.config["PORT"])

    elif app.config["ENV"] == EdifyEnvironments.LOCAL.value:
        print("Running locally...\n")
        app.run(debug=False)

    elif app.config["ENV"] == EdifyEnvironments.TEST.value:
        print("Running tests...\n")
        app.run(debug=True)

    else:
        print("Invalid environment.")
