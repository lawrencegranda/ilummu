from flask import jsonify
from edify.utils.constants import ErrorType
import re
from datetime import datetime, timedelta
import random
import json
import random


def error_response(message: str, error_type: ErrorType) -> tuple:
    """
    Helper function to create a standard error JSON response.
    """
    return (
        jsonify({"errors": message, "type": error_type.name}),
        error_type.value,
    )


phone_regex = re.compile(r"^\+\d{1,2}\s\d{9,15}$")
email_regex = re.compile(r"^[\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}$")


def validate_phone(phone):
    return phone_regex.match(phone)


def validate_email(email):
    return email_regex.match(email)


def validate_date(date):
    try:
        datetime.strptime(graduation_date, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def load_username_data(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


# Load data from JSON file
username_data = load_username_data("edify/static/username_data.json")


def generate_funny_username(n):
    adjectives = username_data["adjectives"]
    nouns = username_data["nouns"]

    adjective = random.choice(adjectives)
    noun = random.choice(nouns)

    n = random.randint(4, n + 1)
    suffix = f"{random.randint(0, 10**n - 1):0{n}d}"

    username = f"{adjective}{noun}{suffix}"
    return username
