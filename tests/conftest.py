"""Test fixtures and configuration for the Edify platform."""

# Standard Library imports
import os
from random import choices
import string

# Third-Party Framework imports
from faker import Faker
import pytest
from flask import Flask
from flask.ctx import RequestContext

# Local Application imports
from edify.database.populate import populate_constants
from edify.models import User, School, Major, Question, Method, Course, Offer
from edify.core import db
from edify.utils.utils import validate_phone
from tests.test_app import create_test_app
from tests.utils import get_jwt_header

# Initialize Faker for generating fake data
fake = Faker()


@pytest.fixture(scope="session")
def app():
    """Create test Flask application."""
    flask_app = create_test_app()
    yield flask_app

    if os.path.exists("instance/site.db"):
        os.remove("instance/site.db")


@pytest.fixture
def client(app: Flask):
    """Create test client with application context."""
    test_client = app.test_client()
    ctx: RequestContext = app.test_request_context()
    ctx.push()
    yield test_client
    ctx.pop()


@pytest.fixture
def client_with_db(client: Flask):
    """Create test client with empty database."""
    db.create_all()
    yield client
    db.drop_all()


@pytest.fixture
def client_with_data(client_with_db: Flask):
    """Create test client with populated database constants."""
    populate_constants()
    return client_with_db


def create_user() -> User:
    """Create a test user with random valid data."""
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
def user_jwt(client_with_data: Flask):
    """Create test user and return with JWT token."""
    user = create_user()
    jwt_header = get_jwt_header(user)
    return user, jwt_header


@pytest.fixture
def client_with_question(client_with_data: Flask):
    """Create test client with a sample question."""
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
def client_with_offer(client_with_question: Flask):
    """Create test client with a sample offer."""
    user = create_user()

    question = (
        db.session.query(Question)
        .filter(
            Question.user_id != user.id,
            Question.visible.is_(True),
            Question.solved.is_(False),
        )
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
