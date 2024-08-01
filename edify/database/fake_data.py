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

# Initialize Faker for generating fake data
fake = Faker()


def generate_test_users(num_users):
    """Generate test users for the database."""
    # Retrieve the specific school and all majors from the database
    school = db.session.query(School).filter_by(name="Cornell University").first()
    majors = db.session.query(Major).all()

    # Loop to create the specified number of test users
    for i in range(num_users):
        # Generate a valid phone number, ensuring it's unique and valid
        phone = f"+1 {''.join(choices(string.digits, k=10))}"
        while (
            not validate_phone(phone)
            or db.session.query(User).filter_by(phone=phone).first()
        ):
            phone = f"+1 {''.join(choices(string.digits, k=10))}"

        # Generate a unique email based on the school email postfix
        email = f"user{i}@{school.email_postfix}"

        # Skip to the next iteration if email already exists
        if db.session.query(User).filter_by(email=email).first():
            continue

        # Hash the password for the user before saving
        password = User.hash_password(f"password_user{i}")
        print(f"password_user{i}")

        # Create a new user instance with the fake data
        user = User(
            username=fake.user_name(),
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            school_id=school.id,
            major_id=choice(majors).id,
            graduation=fake.future_date(end_date="+4y"),
            email=email,
            phone=phone,
            password=password,
            mail_is_verified=fake.boolean(),
            phone_is_verified=fake.boolean(),
            is_mock=False,
            is_test=True,
        )
        db.session.add(user)
    return


def generate_fake_users(num_users):
    """Generate fake users for testing purposes."""
    school = db.session.query(School).filter_by(name="Cornell University").first()
    majors = db.session.query(Major).all()

    # Loop to create the specified number of fake users
    for _ in range(num_users):
        # Generate a valid phone number
        phone = f"+1 {''.join(choices(string.digits, k=10))}"
        while (
            not validate_phone(phone)
            or db.session.query(User).filter_by(phone=phone).first()
        ):
            phone = f"+1 {''.join(choices(string.digits, k=10))}"

        # Generate a password using Faker
        password = User.hash_password(fake.password(length=12))

        # Create a new user instance with the fake data
        user = User(
            username=fake.user_name(),
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            school_id=school.id,
            major_id=choice(majors).id,
            graduation=fake.future_date(end_date="+4y"),
            email=fake.email(),
            phone=phone,
            password=password,
            mail_is_verified=fake.boolean(),
            phone_is_verified=fake.boolean(),
            is_mock=True,
        )
        db.session.add(user)
    return


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

    offers = []
    for _ in range(num_offers):
        # Randomly select a user and a question
        user_id = choice(users).id
        question_id = choice(questions).id
        status = choice(OfferStatusEnum.keys())
        active = not (status in OfferStatusEnum.inactive)

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
            active = not (status in OfferStatusEnum.inactive)

        # Create a new Offer instance with randomized data
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


# Add more functions for other models (AcademicField, Method, TimeInterval, Course, School, NotificationType) if needed


def populate_fake():
    """Populate the database with fake data."""
    # Define the number of each type of data to generate
    num_test_users = 3
    num_users = 5
    num_questions = 20
    num_offers = 30
    num_notifications = 15

    # Use a database session to bulk add mock data
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
