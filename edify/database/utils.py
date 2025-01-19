"""This module contains utility functions for generating fake data for testing purposes."""

# Standard Library imports
import string
from random import choice, choices
from typing import Optional, Tuple

# Third-Party Framework imports
from faker import Faker

# Local Application imports
from edify import db
from edify.models import User, School, Major
from edify.utils.utils import validate_phone

# Initialize Faker for generating fake data
fake = Faker()


def _generate_username() -> str:
    """Generate a valid username."""
    username = fake.user_name()
    while db.session.query(User).filter_by(username=username).first():
        username = fake.user_name()
    return username


def _generate_phone() -> str:
    """Generate a valid phone number."""
    phone = f"+1 {''.join(choices(string.digits, k=10))}"
    while (
        not validate_phone(phone)
        or db.session.query(User).filter_by(phone=phone).first()
    ):
        phone = f"+1 {''.join(choices(string.digits, k=10))}"
    return phone


def create_user(
    school: School, majors: list[Major], is_test=False, i: int = 0
) -> Optional[Tuple[User, str, str]]:
    """Create a test user with random valid data."""

    # Generate a valid username
    username = f"testUser{i}" if is_test else _generate_username()

    # Check if username already exists
    if db.session.query(User).filter_by(username=username).first():
        return None

    # Generate a valid email
    email = f"{username}@{school.email_postfix}"

    # Check if email already exists
    if db.session.query(User).filter_by(email=email).first():
        return None

    # Generate a valid phone number
    phone = _generate_phone()

    # Generate a valid password
    password = f"password_user{i}" if is_test else fake.password(length=12)

    # Create user with fake data
    return (
        User(
            username=username,
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            school_id=school.id,
            major_id=choice(majors).id,
            graduation=fake.future_date(end_date="+4y"),
            email=email,
            phone=phone,
            password=User.hash_password(password),
            mail_is_verified=True,
            phone_is_verified=True,
            is_mock=not is_test,
            is_test=is_test,
        ),
        username,
        password,
    )
