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
from edify.utils.constants import SupportedLanguagesEnum, AuthLevelEnum, OfferStatusEnum
from edify.utils.utils import validate_phone
import string

fake = Faker()


def generate_test_users(num_users):
    school = db.session.query(School).filter_by(name="Cornell University").first()
    majors = db.session.query(Major).all()

    for i in range(num_users):
        phone = f"+1 {''.join(choices(string.digits, k=10))}"
        while (
            not validate_phone(phone)
            or db.session.query(User).filter_by(phone=phone).first()
        ):
            phone = f"+1 {''.join(choices(string.digits, k=10))}"

        email = f"user{i}@{school.email_postfix}"

        if db.session.query(User).filter_by(email=email).first():
            continue

        user = User(
            username=fake.user_name(),
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            school_id=school.id,
            major_id=choice(majors).id,
            graduation=fake.future_date(end_date="+4y"),
            email=f"user{i}@{school.email_postfix}",
            phone=phone,
            password=f"password_user{i}",
            mail_is_verified=fake.boolean(),
            phone_is_verified=fake.boolean(),
            is_mock=True,
            is_test=True,
        )
        db.session.add(user)
    return


def generate_fake_users(num_users):
    school = db.session.query(School).filter_by(name="Cornell University").first()
    majors = db.session.query(Major).all()

    for _ in range(num_users):
        phone = f"+1 {''.join(choices(string.digits, k=10))}"
        while (
            not validate_phone(phone)
            or db.session.query(User).filter_by(phone=phone).first()
        ):
            phone = f"+1 {''.join(choices(string.digits, k=10))}"

        user = User(
            username=fake.user_name(),
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            school_id=school.id,
            major_id=choice(majors).id,
            graduation=fake.future_date(end_date="+4y"),
            email=fake.email(),
            phone=phone,
            password=fake.password(length=12),
            mail_is_verified=fake.boolean(),
            phone_is_verified=fake.boolean(),
            is_mock=True,
        )
        db.session.add(user)
    return


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
        user_id = choice(users).id
        question_id = choice(questions).id
        status = choice(OfferStatusEnum.values())
        active = not (status in OfferStatusEnum.inactive)

        while (
            db.session.query(Offer)
            .filter_by(user_id=user_id, question_id=question_id, active=active)
            .first()
        ):
            user_id = choice(users).id
            question_id = choice(questions).id
            status = choice(OfferStatusEnum.values())
            active = not (status in OfferStatusEnum.inactive)

        offer = Offer(
            user_id=user_id,
            question_id=question_id,
            amount=randint(5, 100),
            status=status,
            active=active,
        )
        db.session.add(offer)
    return


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


def populate_fake():
    num_test_users = 3
    num_users = 5
    num_questions = 20
    num_offers = 30
    num_notifications = 15

    # Generate mock data
    # Add mock data to the database
    with db.session.begin():
        generate_test_users(num_test_users)

        generate_fake_users(num_users)

        questions = generate_fake_questions(num_questions)
        db.session.add_all(questions)

        generate_fake_offers(num_offers)

        notifications = generate_fake_notifications(num_notifications)
        db.session.add_all(notifications)

    print("Database populated with mock data.")


if __name__ == "__main__":
    populate_database()
