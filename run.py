from edify import create_app
from edify.config import Config

application = create_app(Config)
if __name__ == "__main__":
    application.run(debug=True)
