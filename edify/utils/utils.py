from flask import jsonify
from constants import ErrorType


def error_response(message: str, error_type: ErrorType, status_code: int) -> tuple:
    """
    Helper function to create a standard error JSON response.
    """
    return (
        jsonify(
            {"error": message, "type": error_type.value, "status_code": status_code}
        ),
        status_code,
    )
