"""
This script is used to create fake data for the database.
"""

# Third-Party Framework Imports
from sqlalchemy.orm import Session

# Local Application imports
from app import app
from edify.database.setup_base import DatabaseSetup
from edify.database.fake_data import populate_fake


class FakeDataSetup(DatabaseSetup):
    """Database setup including fake data population."""

    def additional_setup(self, db: Session):
        """Add fake data to the database."""
        populate_fake()
        db.session.commit()
        print("Created fake data.")


# Run the Flask app
if __name__ == "__main__":
    setup = FakeDataSetup(app)
    setup.setup()
