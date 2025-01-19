"""
This module contains utility functions for handling database operations.
"""

# Standard Library imports
from typing import Optional

# Third-Party Framework imports
from flask.typing import ResponseReturnValue
from sqlalchemy.exc import IntegrityError

# Local Application imports
from edify import db
from edify.models import Notification
from edify.utils.constants import ErrorType
from edify.utils.utils import error_response


def commit_changes(error_msg: str) -> Optional[ResponseReturnValue]:
    """
    Commit changes and handle potential errors.

    This utility function attempts to commit changes to the database and handles any
    IntegrityError exceptions that may occur during the commit process.
    """
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f"IntegrityError: {e}")
        return error_response(error_msg, ErrorType.INTERNAL_ERROR)
    return None


def create_notification(
    notification_type: str, message: str, user_id: int, question_id: int
) -> Optional[ResponseReturnValue]:
    """Create and commit a notification"""
    notification = Notification(
        type=notification_type,
        message=message,
        user_id=user_id,
        question_id=question_id,
    )
    db.session.add(notification)

    return commit_changes("Failed to create notification")
