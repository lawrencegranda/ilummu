"""
This script is used to create the database and populate it with initial data.
"""

# Third-Party Framework Imports
from sqlalchemy.orm import Session

# Local Application imports
from app import app
from edify.database.setup_base import DatabaseSetup


class BasicSetup(DatabaseSetup):
    """Basic database setup with just constants."""

    def additional_setup(self, db: Session):
        """No additional setup needed."""


# Run the Flask app
if __name__ == "__main__":
    setup = BasicSetup(app)
    setup.setup()
