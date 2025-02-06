"""This module contains functions to generate fake data for testing purposes."""

# Standard Library imports
from random import choice, randint

# Third-Party Framework imports
from faker import Faker

# Local Application imports
from edify.core import db
from edify.models import (
    Course,
    Major,
    Notification,
    NotificationType,
    Offer,
    Question,
    School,
    TimeInterval,
    User,
    Method,
)
from edify.utils.constants import OfferStatusEnum
from edify.database.utils import create_user


# Initialize Faker for generating fake data
fake = Faker()


def generate_fake_users(num_users):
    """Generate fake users for testing purposes."""
    school = db.session.query(School).filter_by(name="Cornell University").first()
    majors = db.session.query(Major).all()

    # Loop to create the specified number of fake users
    for _ in range(num_users):
        user = create_user(school, majors, is_test=False)
        if user:
            db.session.add(user)


def generate_fake_questions(num_questions):
    """Generate fake questions associated with users, courses, and methods."""
    intervals = db.session.query(TimeInterval).all()
    users = db.session.query(User).all()
    methods = db.session.query(Method).all()
    courses = db.session.query(Course).all()

    questions = []
    for _ in range(num_questions):
        # Create a new Question instance with randomized data
        question = Question(
            user_id=choice(users).id,
            course_id=choice(courses).id,
            request=fake.text(max_nb_chars=200),
            solve_time=choice(intervals).value,
            price=randint(5, 100),
            method_id=choice(methods).id,
            solved=fake.boolean(),
        )
        questions.append(question)
    return questions


def generate_fake_offers(num_offers):
    """Generate fake offers associated with users and questions."""
    users = db.session.query(User).all()
    questions = db.session.query(Question).all()

    for _ in range(num_offers):
        # Randomly select a user and a question
        user_id = choice(users).id
        question_id = choice(questions).id
        status = choice(OfferStatusEnum.keys())
        active = not status in OfferStatusEnum.inactive

        # Ensure that the combination of user and question is unique and active
        while (
            db.session.query(Offer)
            .filter_by(user_id=user_id, question_id=question_id, active=active)
            .first()
        ):
            # Re-select user and question if the offer already exists
            user_id = choice(users).id
            question_id = choice(questions).id
            status = choice(OfferStatusEnum.keys())
            active = not status in OfferStatusEnum.inactive

        # Create a new Offer instance with randomized data
        offer = Offer(
            user_id=user_id,
            question_id=question_id,
            amount=randint(5, 100),
            status=status,
            active=active,
        )
        db.session.add(offer)


def generate_fake_notifications(num_notifications):
    """Generate fake notifications for users."""
    users = db.session.query(User).all()
    types = db.session.query(NotificationType).all()
    questions = db.session.query(Question).all()

    notifications = []
    for _ in range(num_notifications):
        notification_type = choice(types)

        question_id = None
        if notification_type.question_required:
            # Randomly select a question if the notification type requires it
            question_id = choice(questions).id

        # Create a new Notification instance with randomized data
        notification = Notification(
            user_id=choice(users).id,
            message=fake.text(max_nb_chars=200),
            type=notification_type.value,
            question_id=question_id,
            link=fake.url(),
        )
        notifications.append(notification)
    return notifications


def populate_fake():
    """Populate the database with fake data."""
    # Define the number of each type of data to generate
    num_users = 5
    num_questions = 20
    num_offers = 30
    num_notifications = 15

    # Use a database session to bulk add mock data
    with db.session.begin():
        generate_fake_users(num_users)

        questions = generate_fake_questions(num_questions)
        db.session.add_all(questions)

        generate_fake_offers(num_offers)

        notifications = generate_fake_notifications(num_notifications)
        db.session.add_all(notifications)

    print("Database populated with mock data.")


if __name__ == "__main__":
    populate_fake()
