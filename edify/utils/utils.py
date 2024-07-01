from flask import jsonify
from edify.utils.constants import ErrorType
import re


def error_response(message: str, error_type: ErrorType) -> tuple:
    """
    Helper function to create a standard error JSON response.
    """
    return (
        jsonify({"error": message, "type": error_type.name}),
        error_type.value,
    )


phone_regex = re.compile(r"^\+\d{1,2}\s\d{9,15}$")
email_regex = re.compile(r"^[\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}$")


def validate_phone(phone):
    return phone_regex.match(phone)


def validate_email(email):
    return email_regex.match(email)
