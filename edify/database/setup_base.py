"""Base setup functionality for database initialization."""

# Standard Library imports
from abc import ABC, abstractmethod

# Third-Party Framework Imports
from sqlalchemy.orm import Session


class DatabaseSetup(ABC):
    """Abstract base class for database setup."""

    def __init__(self, app):
        self.app = app

    def setup(self):
        """Run the database setup process."""
        with self.app.app_context():
            # pylint: disable=import-outside-toplevel
            from edify.core import db
            from edify.database.populate import populate_constants

            # pylint: enable=all

            # Create tables
            db.create_all()
            db.session.commit()
            print("Created database models.")

            # Add constants
            populate_constants()
            db.session.commit()
            print("Added constants.")

            # Run additional setup if needed
            self.additional_setup(db)

    @abstractmethod
    def additional_setup(self, db: Session):
        """Additional setup steps to be implemented by subclasses."""
