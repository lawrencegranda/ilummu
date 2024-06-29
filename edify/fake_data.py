from faker import Faker
from random import choice, randint, choices
from edify import db
from edify.models import (
    User,
    Question,
    Offer,
    Notification,
    AcademicField,
    Method,
    TimeInterval,
    Course,
    School,
    NotificationType,
    Major,
)
from edify.constants import SupportedLanguages, AuthLevel, OfferStatus
import string

fake = Faker()


def generate_fake_users(num_users):
    school = db.session.query(School).filter_by(name="Cornell University").first()
    majors = db.session.query(Major).all()

    users = []
    for _ in range(num_users):
        user = User(
            username=fake.user_name(),
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            school_id=school.id,
            major_id=choice(majors).id,
            graduation=fake.future_date(end_date="+4y"),
            email=fake.email(),
            phone=f"+1 {''.join(choices(string.digits, k=9))}",
            password=fake.password(length=12),
            token=fake.sha256(),
            token_last_refresh=fake.date_time_between(start_date="-1y", end_date="now"),
            mail_is_verified=fake.boolean(),
            phone_is_verified=fake.boolean(),
            is_mock=True,
        )
        users.append(user)
    return users


def generate_fake_questions(num_questions):
    intervals = db.session.query(TimeInterval).all()
    users = db.session.query(User).all()
    methods = db.session.query(Method).all()
    courses = db.session.query(Course).all()

    questions = []
    for _ in range(num_questions):
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
    users = db.session.query(User).all()
    questions = db.session.query(Question).all()

    offers = []
    for _ in range(num_offers):
        offer = Offer(
            user_id=choice(users).id,
            question_id=choice(questions).id,
            amount=randint(5, 100),
            status=choice(list(OfferStatus)),
        )
        offers.append(offer)
    return offers


def generate_fake_notifications(num_notifications):
    users = db.session.query(User).all()
    types = db.session.query(NotificationType).all()
    questions = db.session.query(Question).all()

    notifications = []
    for _ in range(num_notifications):
        notification_type = choice(types)

        question_id = None
        if notification_type.question_required:
            question_id = choice(questions).id

        notification = Notification(
            user_id=choice(users).id,
            message=fake.text(max_nb_chars=200),
            type_id=notification_type.id,
            question_id=question_id,
            link=fake.url(),
        )
        notifications.append(notification)
    return notifications


# Add more functions for other models (AcademicField, Method, TimeInterval, Course, School, NotificationType) if needed


def populate_database():
    num_users = 10
    num_questions = 20
    num_offers = 30
    num_notifications = 15

    # Generate mock data
    # Add mock data to the database
    with db.session.begin():
        users = generate_fake_users(num_users)
        db.session.add_all(users)

        questions = generate_fake_questions(num_questions)
        db.session.add_all(questions)

        offers = generate_fake_offers(num_offers)
        db.session.add_all(offers)

        notifications = generate_fake_notifications(num_notifications)
        db.session.add_all(notifications)

    print("Database populated with mock data.")


if __name__ == "__main__":
    populate_database()
