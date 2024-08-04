# tests/conftest.py: Pytest configuration file
# Specifies the client fixtures used for testing.

# Standard Library imports
import os

# Third-Party Framework imports
from faker import Faker
from flask_jwt_extended import create_access_token
import pytest

# Local Application imports
from edify.database.populate import populate_constants
from edify.models import *
from edify import db
from tests.test_app import create_test_app

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


@pytest.fixture
def jwt_headers(client):
    user = User(
        username="testuser",
        email="test@example.com",
        password="hashed_password",
        firstname="Test",
        lastname="User",
        phone="+1 9363638567",
        school_id=1,
        major_id=1,
        graduation=fake.future_date(end_date="+4y"),
    )
    db.session.add(user)
    db.session.commit()

    # Create and return a JWT token for the user
    access_token = create_access_token(identity=user.id)

    return {"Authorization": f"Bearer {access_token}"}
