from faker import Faker
from random import choice, randint
from datetime import datetime, timedelta
from edify import db
from edify.models import (
    User,
    Question,
    Offer,
    Notification,
    Subject,
    Method,
    TimeInterval,
    Course,
    School,
    NotificationType,
)
from edify.constants import SupportedLanguages, AuthLevel

fake = Faker()


def generate_fake_users(num_users):
    users = []
    for _ in range(num_users):
        user = User(
            username=fake.user_name(),
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            school=fake.company(),
            major=fake.job(),
            graduation=fake.future_date(end_date="+4y"),
            email=fake.email(),
            phone=fake.phone_number(),
            password=fake.password(length=12),
            created_at=fake.date_time_between(start_date="-1y", end_date="now"),
            updated_at=fake.date_time_between(start_date="-1y", end_date="now"),
            token=fake.sha256(),
            token_last_refresh=fake.date_time_between(start_date="-1y", end_date="now"),
            auth_level=randint(0, 5),
            mail_is_verified=fake.boolean(),
            phone_is_verified=fake.boolean(),
            is_mock=True,
            language=choice(list(SupportedLanguages)),
            image_file=fake.file_name(category="image"),
        )
        users.append(user)
    return users


def generate_fake_questions(num_questions, users):
    questions = []
    for _ in range(num_questions):
        question = Question(
            user_id=choice(users).id,
            course_id=randint(
                1, 10
            ),  # Replace with actual course IDs from your database
            request=fake.text(max_nb_chars=200),
            solve_time=randint(5, 120),
            price=randint(5, 100),
            method_id=randint(
                1, 3
            ),  # Replace with actual method IDs from your database
            solved=fake.boolean(),
            created_at=fake.date_time_between(start_date="-1y", end_date="now"),
            updated_at=fake.date_time_between(start_date="-1y", end_date="now"),
        )
        questions.append(question)
    return questions


def generate_fake_offers(num_offers, users, questions):
    offers = []
    for _ in range(num_offers):
        offer = Offer(
            user_id=choice(users).id,
            question_id=choice(questions).id,
            amount=randint(5, 100),
            status=choice(["SENT", "ACCEPTED", "DECLINED"]),
            created_at=fake.date_time_between(start_date="-1y", end_date="now"),
            updated_at=fake.date_time_between(start_date="-1y", end_date="now"),
        )
        offers.append(offer)
    return offers


def generate_fake_notifications(num_notifications, users):
    notifications = []
    for _ in range(num_notifications):
        notification = Notification(
            user_id=choice(users).id,
            message=fake.text(max_nb_chars=200),
            type_id=randint(
                1, 5
            ),  # Replace with actual notification type IDs from your database
            link=fake.url(),
            created_at=fake.date_time_between(start_date="-1y", end_date="now"),
        )
        notifications.append(notification)
    return notifications


# Add more functions for other models (Subject, Method, TimeInterval, Course, School, NotificationType) if needed


def populate_database():
    num_users = 10
    num_questions = 20
    num_offers = 30
    num_notifications = 15

    # Generate mock data
    users = generate_fake_users(num_users)
    questions = generate_fake_questions(num_questions, users)
    offers = generate_fake_offers(num_offers, users, questions)
    notifications = generate_fake_notifications(num_notifications, users)

    # Add mock data to the database
    with db.session.begin():
        db.session.add_all(users)
        db.session.add_all(questions)
        db.session.add_all(offers)
        db.session.add_all(notifications)

    print("Database populated with mock data.")


if __name__ == "__main__":
    populate_database()
