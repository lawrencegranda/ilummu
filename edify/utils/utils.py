from edify.utils.constants import ErrorType
import re
from datetime import datetime, timedelta
import random
import json
import phonenumbers
from flask import jsonify, current_app, url_for, request
from werkzeug.test import EnvironBuilder


# Extracts the access token from the request headers
def get_access_header(request):
    """
    Extracts the access token from the request headers.

    Args:
        request (flask.Request): The incoming HTTP request object.

    Returns:
        str: The access token if present, otherwise None.
    """
    token = None

    if "HTTP_AUTHORIZATION" in request.environ:
        auth_header = request.headers.get("Authorization")
        token = (
            auth_header.split(" ")[1] if auth_header and " " in auth_header else None
        )

    return token


# Extracts the access token from the request, either from headers or cookies
def get_request_cookie(request):
    """
    Extracts the access token from the request, either from headers or cookies.

    Args:
        request (flask.Request): The incoming HTTP request object.

    Returns:
        str: The access token if present, otherwise None.
    """
    token = get_access_header(request)
    if token:
        return token

    token = request.cookies.get("access_token_cookie")
    if token:
        return token

    return None


# Creates an internal request within the Flask application using test request context
def internal_request(url, method="GET"):
    """
    Creates an internal request within the Flask application using test request context.

    Args:
        url (str): The URL to request.
        method (str, optional): The HTTP method to use. Defaults to "GET".

    Returns:
        flask.Response: The response from the requested URL.
    """
    # Build the environment
    builder = EnvironBuilder(path=url, method=method)
    env = builder.get_environ()
    env["HTTP_COOKIE"] = ""

    # Check if the user has a JWT token cookie and add it to the environment
    token = get_request_cookie(request)
    if token:
        env["HTTP_COOKIE"] = f"access_token_cookie={token}"

    # Check if the user has a JWT refresh token
    refresh_token = request.cookies.get("refresh_token_cookie")
    if refresh_token:
        env["HTTP_COOKIE"] = (
            f'{env["HTTP_COOKIE"]}; refresh_token_cookie={refresh_token}'
        )

    # Create the test request context with the environment
    with current_app.test_request_context(environ_overrides=env):
        response = current_app.full_dispatch_request()

    return response


# Returns a JSON response with an error message and error type
def error_response(message: str, error_type: ErrorType) -> tuple:
    """
    Helper function to create a standard error JSON response.

    Args:
        message (str): The error message to return.
        error_type (ErrorType): The type of error.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.
    """
    return (
        jsonify({"errors": message, "type": error_type.name}),
        error_type.value,
    )


# Regex pattern to validate an email address
email_regex = re.compile(
    r"^[a-zA-Z0-9]([\w\-\.])+@[a-zA-Z0-9]+[\w\-\.]*\w\.[a-zA-Z]{2,6}$"
)
validate_email = lambda x: email_regex.match(x)

# Regex pattern to validate an email domain
email_postfix_regex = re.compile(r"^[a-zA-Z0-9]+[\w\-\.]*\w\.[a-zA-Z]{2,6}$")
validate_email_postfix = lambda x: email_postfix_regex.match(x)


# Validates a phone number using the phonenumbers library
def validate_phone(phone):
    """
    Validates a phone number using the phonenumbers library.

    Args:
        phone (str): The phone number to validate.

    Returns:
        bool: True if the phone number is valid, otherwise False.
    """
    try:
        # Parse the phone number
        parsed_number = phonenumbers.parse(phone, None)

        # Check if the number is valid
        return phonenumbers.is_valid_number(parsed_number)
    except:
        return False


# Formats a phone number to international format if it is valid
def format_phone(phone):
    """
    Formats a phone number to international format if it is valid.

    Args:
        phone (str): The phone number to format.

    Returns:
        str: The formatted phone number, or the original phone number if invalid.
    """
    if not validate_phone(phone):
        return phone

    parsed_number = phonenumbers.parse(phone, None)
    phone = phonenumbers.format_number(
        parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
    )

    return phone


# Validates a date string in the format YYYY-MM-DD
def validate_date(date):
    """
    Validates a date string in the format YYYY-MM-DD.

    Args:
        date (str): The date string to validate.

    Returns:
        bool: True if the date is valid, otherwise False.
    """
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# Loads username data from a JSON file
def load_username_data(file_path):
    """
    Loads username data from a JSON file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The loaded username data.
    """
    with open(file_path, "r") as file:
        return json.load(file)


# Generates a funny username using adjectives and nouns from the loaded data
def generate_funny_username(n):
    """
    Generates a funny username using adjectives and nouns from the loaded data.

    Args:
        n (int): The maximum length of the numeric suffix.

    Returns:
        str: The generated funny username.
    """

    # Load data from JSON file
    username_data = load_username_data("edify/static/username_data.json")

    adjectives = username_data["adjectives"]
    nouns = username_data["nouns"]

    adjective = random.choice(adjectives)
    noun = random.choice(nouns)

    n = random.randint(4, n + 1)
    suffix = f"{random.randint(0, 10**n - 1):0{n}d}"

    username = f"{adjective}{noun}{suffix}"
    return username


# Strips leading and trailing whitespace from a string
def format_strip(target, value, oldvalue, initiator):
    """
    Strips leading and trailing whitespace from a string.

    Args:
        target: Unused parameter.
        value (str): The string to strip.
        oldvalue: Unused parameter.
        initiator: Unused parameter.

    Returns:
        str: The stripped string.
    """
    return value.strip()


# Converts a string to title case
format_title_case = lambda *x: format_strip(*x).title()

# Converts a string to lower case
format_lower_case = lambda *x: format_strip(*x).lower()

# Converts a string to upper case
format_upper_case = lambda *x: format_strip(*x).upper()


# Determines the college year based on the given date
def get_college_year(date: datetime.date) -> str:
    """
    Determines the college year based on the given date.

    Args:
        date (datetime.date): The date to calculate the college year from.

    Returns:
        str: The college year as a string (e.g., 'Senior', 'Junior').
    """
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


# Returns a human-readable string representing the time difference from the given date to now
def get_time_ago(date: datetime) -> str:
    """
    Returns a human-readable string representing the time difference from the given date to now.

    Args:
        date (datetime): The date to calculate the time difference from.

    Returns:
        str: The time difference as a human-readable string (e.g., '5 minutes ago').
    """
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


# Trims a string to a specified length and appends ellipsis if the string exceeds the length
def trim_text(string: str, length: int):
    """
    Trims a string to a specified length and appends ellipsis if the string exceeds the length.

    Args:
        string (str): The string to trim.
        length (int): The maximum length of the string.

    Returns:
        str: The trimmed string with ellipsis if it exceeds the length.
    """
    return string[0:length] + "..." if len(string) > length + 3 else string
