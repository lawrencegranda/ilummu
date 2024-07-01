from edify import create_app
from edify.config import Config
from edify.models import *

# Create the Flask app
app = create_app(Config)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
