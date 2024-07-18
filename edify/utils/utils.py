from edify.utils.constants import ErrorType
import re
from datetime import datetime, timedelta
import random
import json
import random
import phonenumbers
from flask import jsonify, current_app, url_for, request
from werkzeug.test import EnvironBuilder


def internal_request(url, method="GET"):
    # Build the environment
    builder = EnvironBuilder(path=url, method=method)
    env = builder.get_environ()

    # Check if the user has a JWT token cookie and add it to the environment
    token = request.cookies.get("access_token_cookie")
    if token:
        env["HTTP_COOKIE"] = f"access_token_cookie={token}"

    # Create the test request context with the environment
    with current_app.test_request_context(environ_overrides=env):
        response = current_app.full_dispatch_request()

    # Parse the response
    data, status = response.get_json(), response.status_code

    return data, status


def error_response(message: str, error_type: ErrorType) -> tuple:
    """
    Helper function to create a standard error JSON response.
    """
    return (
        jsonify({"errors": message, "type": error_type.name}),
        error_type.value,
    )


email_regex = re.compile(
    r"^[a-zA-Z0-9]([\w\-\.])+@[a-zA-Z0-9]+[\w\-\.]*\w\.[a-zA-Z]{2,6}$"
)
validate_email = lambda x: email_regex.match(x)

email_postfix_regex = re.compile(r"^[a-zA-Z0-9]+[\w\-\.]*\w\.[a-zA-Z]{2,6}$")
validate_email_postfix = lambda x: email_postfix_regex.match(x)


def validate_phone(phone):
    try:
        # Parse the phone number
        parsed_number = phonenumbers.parse(phone, None)

        # Check if the number is valid
        return phonenumbers.is_valid_number(parsed_number)
    except:
        return False


def format_phone(phone):
    if not validate_phone(phone):
        return phone

    parsed_number = phonenumbers.parse(phone, None)
    phone = phonenumbers.format_number(
        parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
    )

    return phone


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


def format_strip(target, value, oldvalue, initiator):
    return value.strip()


format_title_case = lambda *x: format_strip(*x).title()
format_lower_case = lambda *x: format_strip(*x).lower()
format_upper_case = lambda *x: format_strip(*x).upper()


def get_college_year(date: datetime.date) -> str:
    current = datetime.today()

    delta_years = (date - current).days / 365.0

    if delta_years < 0 or delta_years > 4:
        return f"Class of '{date.year.__repr__()[-2:]}"
    if delta_years < 1:
        return f"Senior"
    if delta_years < 2:
        return f"Junior"
    if delta_years < 3:
        return f"Sophomore"
    else:
        return f"Freshman"


def get_time_ago(date: datetime) -> str:
    current = datetime.utcnow()
    diff = current - date

    if diff < timedelta(minutes=1):
        return "Just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() // 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff < timedelta(days=2):
        return "Yesterday"
    elif diff < timedelta(weeks=1):
        days = diff.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif diff < timedelta(weeks=2):
        return "Last week"
    elif diff < timedelta(weeks=4):
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif diff < timedelta(days=60):
        return "Last month"
    elif diff < timedelta(days=365):
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff < timedelta(years=2):
        return "Last year"
    else:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"


def trim_text(string: str, length: int):
    return string[0:length] + "..." if len(string) > length + 3 else string
