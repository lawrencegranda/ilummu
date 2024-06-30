from edify import create_app
from edify.config import Config
from edify.models import (
    User,
    Question,
    Offer,
    Notification,
    Major,
    AcademicField,
    Method,
    TimeInterval,
    Course,
    School,
    NotificationType,
)
from edify.populate import populate_constants
from edify import db
from edify.fake_data import populate_fake
from app import app


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

        # Temporary
        populate_fake()
        db.session.commit()
