from edify import create_app
from edify.config import Config
from edify.models import (
    User,
    Question,
    Offer,
    Notification,
    Major,
    Subject,
    Method,
    TimeInterval,
    Course,
    School,
    NotificationType,
)
from edify.populate import (
    populate_universities,
    populate_subjects,
    populate_methods,
    populate_time_intervals,
    populate_notification_types,
    populate_majors,
    populate_courses,
)
from edify import db


# Populate data and commit changes to the database session
def populate_data():
    populate_universities()
    populate_subjects()
    populate_methods()
    populate_time_intervals()
    populate_notification_types()
    populate_majors()
    populate_courses()
    db.session.commit()


# Create the Flask app
app = create_app(Config)

# Run the Flask app
if __name__ == "__main__":

    # Create all tables defined in the SQLAlchemy models
    with app.app_context():
        from edify import db  # Import db within the app context

        db.create_all()
        db.session.commit()

        print("Created database models.")

        populate_universities()
        populate_subjects()
        populate_methods()
        populate_time_intervals()
        populate_notification_types()
        populate_majors()
        populate_courses()

        db.session.commit()

    app.run(debug=True)
