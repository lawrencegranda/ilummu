# Local Application imports
from app import app
from edify import create_app, db
from edify.config import Config
from edify.database.fake_data import populate_fake
from edify.database.populate import populate_constants
from edify.models import (
    AcademicField,
    Course,
    Major,
    Method,
    Notification,
    NotificationType,
    Offer,
    Question,
    School,
    TimeInterval,
    User,
)


# Run the Flask app
if __name__ == "__main__":

    # Create all tables defined in the SQLAlchemy models
    with app.app_context():
        from edify import db  # Import db within the app context

        db.create_all()
        db.session.commit()

        print("Created database models.")

        populate_constants()
        db.session.commit()

        print("Added constants.")
