"""
This script is used to create the database and populate it with initial data.
"""

# Local Application imports
from app import app
from edify.database.populate import populate_constants


# Run the Flask app
if __name__ == "__main__":

    # Create all tables defined in the SQLAlchemy models
    with app.app_context():
        # pylint: disable=import-outside-toplevel
        from edify import db  # Import db within the app context

        db.create_all()
        db.session.commit()

        print("Created database models.")

        populate_constants()
        db.session.commit()

        print("Added constants.")
