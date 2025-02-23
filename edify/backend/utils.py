"""
This module contains utility functions for handling database operations.
"""

# Standard Library imports
from typing import Optional

# Third-Party Framework imports
from flask.typing import ResponseReturnValue
from sqlalchemy.exc import IntegrityError

# Local Application imports
from edify.core import db, socketio
from edify.models import Notification
from edify.utils.constants import ErrorType, NotificationTypeEnum
from edify.utils.utils import error_response


def emit_notification(notification: Notification) -> None:
    """
    Emit a socketio notification to the user's room.
    """
    notification_type_map = {
        NotificationTypeEnum.OFFER_ACCEPTED: "success",
        NotificationTypeEnum.NEW_OFFER: "success",
        NotificationTypeEnum.OFFER_REVOKED: "warning",
        NotificationTypeEnum.PASSWORD_RESET: "warning",
        NotificationTypeEnum.QUESTION_DELETED: "warning",
        NotificationTypeEnum.OFFER_DECLINED: "warning",
    }

    # Determine reload URL based on notification properties
    reload_url = None
    if notification.question_id:
        reload_url = f"/question/{notification.question_id}"
    elif notification.link:
        reload_url = notification.link

    # Emit banner
    socketio.emit(
        "offer_notification",
        {
            "type": notification_type_map.get(notification.type, "info"),
            "message": notification.message,
            "reload_url": reload_url,
        },
        room=f"user_{notification.user_id}",
    )


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
        print(f"ERROR: IntegrityError: {e}")
        return error_response(error_msg, ErrorType.INTERNAL_ERROR)
    return None


# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
def create_notification(
    notification_type: str,
    message: str,
    user_id: int,
    question_id: Optional[int] = None,
    link: Optional[str] = None,
    emit: Optional[bool] = False,
) -> Optional[ResponseReturnValue]:
    """Create and commit a notification"""
    notification = Notification(
        type=notification_type,
        message=message,
        user_id=user_id,
        question_id=question_id,
        link=link,
    )
    db.session.add(notification)

    if emit:
        emit_notification(notification)

    return commit_changes("Failed to create notification")


# pylint: enable=all
