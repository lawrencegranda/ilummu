"""Utility functions for authentication, data formatting, and request handling."""

# Standard Library imports
from http import HTTPStatus
import io
import json
import random
import re
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple, List

# Third-Party Framework Imports
import flask
from flask import current_app, jsonify, request, url_for, redirect
from flask.typing import ResponseReturnValue
from flask_jwt_extended import unset_jwt_cookies
from marshmallow import Schema, ValidationError
import phonenumbers
from werkzeug.test import EnvironBuilder

# Local Application imports
from edify.utils.constants import ErrorType, AuthSchema


# Fetch data from a given backend API endpoint
def fetch_data(url: str, method: str = "GET") -> List[Any]:
    """
    Fetch data from a given backend API endpoint.

    Parameters:
        url (str): Endpoint URL to fetch data from.
        method (str): HTTP method to use (default is "GET").

    Returns:
        List[Any]: Data retrieved from the backend or an empty list if an error occurs.
    """
    response = internal_request(url, method)

    # Parse the response
    data, status = response.get_json(), response.status_code

    if status != HTTPStatus.OK:
        print(f"fetch_data error: {status}")
        return []

    return data.get("data", [])


# Extracts the access token from the request headers
def get_access_header(http_request: flask.Request) -> Optional[str]:
    """
    Extracts the access token from the request headers.

    Args:
        http_request (flask.Request): The incoming HTTP request object.

    Returns:
        str: The access token if present, otherwise None.
    """
    token = None

    if "HTTP_AUTHORIZATION" in http_request.environ:
        auth_header = http_request.headers.get("Authorization")
        token = (
            auth_header.split(" ")[1] if auth_header and " " in auth_header else None
        )

    return token


# Extracts the access token from the request, either from headers or cookies
def get_request_cookie(http_request: flask.Request) -> Optional[str]:
    """
    Extracts the access token from the request, either from headers or cookies.

    Args:
        http_request (flask.Request): The incoming HTTP request object.

    Returns:
        str: The access token if present, otherwise None.
    """
    token = get_access_header(http_request)
    if token:
        return token

    token = http_request.cookies.get("access_token_cookie")
    if token:
        return token

    return None


# Creates an internal request within the Flask application using test request context
def internal_request(
    url: str,
    method: str = "GET",
    data: Any = None,
    is_form: bool = False,
    file: Optional[Tuple[io.BytesIO, str]] = None,
) -> ResponseReturnValue:
    """
    Creates an internal request within the Flask application using test request context.

    Args:
        url (str): The URL to request.
        method (str, optional): The HTTP method to use. Defaults to "GET".
        data (Any, optional): The data to send.
        is_form (bool, optional): Whether to include data as form or not.
        file (Optional[Tuple[io.BytesIO, str]], optional): File to include, as (file_obj, filename).

    Returns:
        flask.Response: The response from the requested URL.
    """
    # Include JWT cookies if present
    token = get_request_cookie(request)

    # Check if the user has a JWT refresh token
    refresh_token = request.cookies.get("refresh_token_cookie", default=None)

    if data and is_form and method == "POST":
        # Prepare form data, including the file if provided
        form = data.copy()
        if file:
            form["image"] = file  # Attach file to form data in Flask format

        # Make request
        with current_app.test_client() as client:
            # Set the cookies on the client
            if token:
                client.set_cookie("localhost", "access_token_cookie", token)
            if refresh_token:
                client.set_cookie("localhost", "refresh_token_cookie", refresh_token)

            # Optionally add headers for authorization, etc.
            headers = {"Authorization": f"Bearer {token}"}

            # Send the POST request with form data and headers
            response = client.post("/backend/question/new", data=form, headers=headers)

        return response

    # Build environment
    builder = EnvironBuilder(path=url, method=method)
    env = builder.get_environ()
    env["HTTP_COOKIE"] = ""

    # Set cookies in the environment
    if token:
        env["HTTP_COOKIE"] = f"access_token_cookie={token}"
    if refresh_token:
        env["HTTP_COOKIE"] = (
            f'{env["HTTP_COOKIE"]}; refresh_token_cookie={refresh_token}'
        )

    # Set up the body depending on data type
    if data and method == "POST":
        # JSON body
        env["wsgi.input"] = io.BytesIO(json.dumps(data).encode("utf-8"))
        env["CONTENT_TYPE"] = "application/json"

        with current_app.test_request_context(environ_overrides=env, json=data):
            response = current_app.full_dispatch_request()

        return response

    # GET or other methods without data
    with current_app.test_request_context(environ_overrides=env):
        response = current_app.full_dispatch_request()

    return response


# Format a response to pass data
def data_response(data: Any = None) -> tuple:
    """
    Helper function to pass data as JSON.

    Args:
        data (Any): The data to return.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.
    """
    # Make a list if not already one
    if data is None:
        data = []
    elif not isinstance(data, list):
        data = [data]

    return jsonify({"data": data}), HTTPStatus.OK


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
    print(f"{error_type.value} {error_type.name}: {message}")
    return (
        jsonify({"msg": message, "type": error_type.name}),
        error_type.value,
    )


# Regex pattern to validate an email address
email_regex = re.compile(
    r"^[a-zA-Z0-9]([\w\-\.])+@[a-zA-Z0-9]+[\w\-\.]*\w\.[a-zA-Z]{2,6}$"
)
validate_email = email_regex.match

# Regex pattern to validate an email domain
email_postfix_regex = re.compile(r"^[a-zA-Z0-9]+[\w\-\.]*\w\.[a-zA-Z]{2,6}$")
validate_email_postfix = email_postfix_regex.match


# Validates a phone number using the phonenumbers library
def validate_phone(phone: str) -> bool:
    """Validates a phone number using the phonenumbers library."""
    try:
        # Parse the phone number
        parsed_number = phonenumbers.parse(phone, None)
        # Check if the number is valid
        return phonenumbers.is_valid_number(parsed_number)
    except phonenumbers.NumberParseException as _:
        return False


# Formats a phone number to international format if it is valid
def format_phone(phone: str) -> Optional[str]:
    """
    Formats a phone number to international format if it is valid.

    Args:
        phone (str): The phone number to format.

    Returns:
        Optional[str]: The formatted phone number, or None if invalid.
    """
    if not validate_phone(phone):
        return None

    parsed_number = phonenumbers.parse(phone, None)
    phone = phonenumbers.format_number(
        parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
    )

    return phone


# Validates a date string in the format YYYY-MM-DD
def validate_date(date: str) -> bool:
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
def load_username_data(file_path: str) -> dict:
    """
    Loads username data from a JSON file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The loaded username data.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# Generates a funny username using adjectives and nouns from the loaded data
def generate_funny_username(n: int) -> str:
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
def format_strip(_target: Any, value: str, _oldvalue: Any, _initiator: Any) -> str:
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
def format_title_case(*x: Any) -> str:
    """Convert string to title case after stripping whitespace."""
    return format_strip(*x).title()


# Converts a string to lower case
def format_lower_case(*x: Any) -> str:
    """Convert string to lower case after stripping whitespace."""
    return format_strip(*x).lower()


# Converts a string to upper case
def format_upper_case(*x: Any) -> str:
    """Convert string to upper case after stripping whitespace."""
    return format_strip(*x).upper()


# Determines the college year based on the given date
def get_college_year(date: datetime) -> str:
    """
    Determines the college year based on the given date.

    Args:
        date (datetime): The date to calculate the college year from.

    Returns:
        str: The college year as a string (e.g., 'Senior', 'Junior').
    """
    current = datetime.today()

    delta_years = (date - current).days / 365.0

    if delta_years < 0 or delta_years > 4:
        return f"Class of '{repr(date.year)[-2:]}"
    if delta_years < 1:
        return "Senior"
    if delta_years < 2:
        return "Junior"
    if delta_years < 3:
        return "Sophomore"

    return "Freshman"


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
    result = ""

    # Handle recent times (less than a day)
    if diff < timedelta(minutes=1):
        result = "Just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() // 60)
        result = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() // 3600)
        result = f"{hours} hour{'s' if hours > 1 else ''} ago"

    # Handle days and weeks
    elif diff < timedelta(days=2):
        result = "Yesterday"
    elif diff < timedelta(weeks=1):
        days = diff.days
        result = f"{days} day{'s' if days > 1 else ''} ago"
    elif diff < timedelta(weeks=2):
        result = "Last week"
    elif diff < timedelta(weeks=4):
        weeks = diff.days // 7
        result = f"{weeks} week{'s' if weeks > 1 else ''} ago"

    # Handle months and years
    elif diff < timedelta(days=60):
        result = "Last month"
    elif diff < timedelta(days=365):
        months = diff.days // 30
        result = f"{months} month{'s' if months > 1 else ''} ago"
    elif diff < timedelta(years=2):
        result = "Last year"
    else:
        years = diff.days // 365
        result = f"{years} year{'s' if years > 1 else ''} ago"

    return result


# Returns a int from the given date to now
def get_seconds_ago(date: datetime) -> int:
    """
    Returns the seconds difference from the given date to now.

    Args:
        date (datetime): The date to calculate the time difference from.

    Returns:
        int: The time difference in seconds.
    """
    current = datetime.utcnow()
    diff = current - date

    return int(diff.total_seconds())


# Trims a string to a specified length and appends ellipsis if the string exceeds the length
def trim_text(string: str, length: int) -> str:
    """
    Trims a string to a specified length and appends ellipsis if the string exceeds the length.

    Args:
        string (str): The string to trim.
        length (int): The maximum length of the string.

    Returns:
        str: The trimmed string with ellipsis if it exceeds the length.
    """
    return string[0:length].strip() + "..." if len(string) > length + 3 else string


# Encode datetime as int
def date_to_int(d: datetime) -> int:
    """Convert datetime to integer format YYYYMMDDHHMMSS."""
    return int(d.strftime("%Y%m%d%H%M%S"))


# Validate password
def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate the password based on the following criteria:
    - At least 8 characters long
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (e.g., !@#$%^&*)

    Args:
        password (str): The password to validate.

    Returns:
        Tuple[bool, str]: True if the password is valid, False otherwise, along with
        a message indicating the result of the validation.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."

    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."

    return True, "Password is valid."


def validate_auth_data(input_data: dict) -> bool:
    """Validates input data against the AuthSchema. Returns true if successful."""
    try:
        # Dynamically create a marshmallow schema from the dictionary
        schema = Schema.from_dict(AuthSchema)()
        _ = schema.load(input_data)  # Validate the input data
        return True
    except ValidationError as e:
        print("ERROR: Encountered an error validating the Auth schema", e)
        return False


def handle_invalid_token() -> ResponseReturnValue:
    """
    Handle invalid or missing JWT tokens by unsetting cookies and redirecting to the logout page.

    Returns:
        Response: A Flask response object that redirects to the logout page
        with JWT cookies cleared.
    """
    response = redirect(url_for("frontend.logout"))
    unset_jwt_cookies(response)
    return response
