# tests/conftest.py: Pytest configuration file
# Specifies the client fixtures used for testing.

# Standard Library imports
import os
from random import choice, randint, choices
import string

# Third-Party Framework imports
from faker import Faker
from flask_jwt_extended import create_access_token
import pytest

# Local Application imports
from edify.database.populate import populate_constants
from edify.database.fake_data import populate_fake
from edify.models import *
from edify import db
from edify.utils.utils import validate_phone
from tests.test_app import create_test_app
from tests.utils import get_jwt_header

# Initialize Faker for generating fake data
fake = Faker()


@pytest.fixture(scope="session")
def app():
    app = create_test_app()

    yield app

    os.remove("instance/site.db")


@pytest.fixture
def client(app):
    client = app.test_client()

    ctx = app.test_request_context()
    ctx.push()

    yield client

    ctx.pop()


@pytest.fixture
def client_with_db(client):
    db.create_all()

    yield client

    db.drop_all()


@pytest.fixture
def client_with_data(client_with_db):
    """
    A fixture to set up constants.
    """
    populate_constants()
    return client_with_db


def create_user() -> User:
    school = db.session.query(School).filter_by(name="Cornell University").first()
    major = db.session.query(Major).first()

    # Generate valid email
    i, username = 1, "user1"
    while db.session.query(User).filter_by(username=username).first():
        i += 1
        username = f"user{i}"

    # Generate a valid phone number, ensuring it's unique and valid
    phone = f"+1 {''.join(choices(string.digits, k=10))}"
    while (
        not validate_phone(phone)
        or db.session.query(User).filter_by(phone=phone).first()
    ):
        phone = f"+1 {''.join(choices(string.digits, k=10))}"

    user = User(
        username=username,
        email=f"{username}@example.com",
        password="password",
        firstname="Test",
        lastname=username,
        phone=phone,
        school_id=school.id,
        major_id=major.id,
        graduation=fake.future_date(end_date="+4y"),
    )

    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture
def user_jwt(client_with_data):
    user = create_user()

    # Create and return a JWT token for the user
    jwt_header = get_jwt_header(user)

    return user, jwt_header


@pytest.fixture
def client_with_question(client_with_data):
    user = create_user()

    method = db.session.query(Method).first()
    course = db.session.query(Course).filter_by(school_id=user.school_id).first()

    # Create a new question associated with the user and course
    question = Question(
        user_id=user.id,
        course_id=course.id,
        request="What is Python?",
        solve_time=10,
        price=45.0,
        method_id=method.id,
        solved=False,
    )

    db.session.add(question)
    db.session.commit()

    return client_with_data


@pytest.fixture
def client_with_offer(client_with_question):
    user = create_user()

    question = (
        db.session.query(Question)
        .filter(Question.user_id != user.id)
        .filter(Question.visible == True)
        .filter(Question.solved == False)
        .first()
    )

    # Create a new offer associated with the user and question
    offer = Offer(
        user_id=user.id,
        question_id=question.id,
        amount=question.price,
    )

    db.session.add(offer)
    db.session.commit()

    return client_with_question
