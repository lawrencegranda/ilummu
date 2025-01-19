"""Notification-related models."""

# Standard Library imports
from datetime import datetime
from typing import Dict, Any

# Third-Party Framework imports
from flask import url_for
from sqlalchemy import Index, event

# Local Application imports
from edify.core import db
from edify.models.base import BaseModel
from edify.utils.constants import NotificationTypeEnum


class NotificationType(BaseModel):
    """
    Table that contains notification type information

    Entries are created to list available notification types.
    """

    # Notification type name
    value = db.Column(db.String(100), primary_key=True)

    # Whether the type requires a link to a question.
    question_required = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"NotificationType({self.value}, {self.question_required})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        return {
            "id": self.id,
            "value": self.name,
            "question_required": self.question_required,
        }

    @staticmethod
    def validator(_mapper, _connection, target):
        """Validate notification type value before insert/update."""
        if not target.value in NotificationTypeEnum.values():
            raise ValueError(
                f'NOTIFICATION TYPE MODEL: Invalid value ("{target.value}").'
            )


# Attach event listeners
event.listen(NotificationType, "before_insert", NotificationType.validator)
event.listen(NotificationType, "before_update", NotificationType.validator)


class Notification(BaseModel):
    """
    Table that contains notification information

    Entries are created when a user needs to be notified.
    """

    __table_args__ = (
        Index("ix_notification_user_id", "user_id"),
        Index("ix_notification_type", "type"),
    )

    # Primary key that identifies the notification
    id = db.Column(db.Integer, primary_key=True)

    # User associated with the notification
    # Many-to-One relationship with User model
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref="notifications", lazy=True)

    # Notification message
    message = db.Column(db.String(200), nullable=False)

    # Type of notification
    type = db.Column(
        db.String(100), db.ForeignKey("notification_type.value"), nullable=False
    )

    # Link to further details
    link = db.Column(db.String(300), nullable=True)

    # Question it relates to, if it does
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=True)
    question = db.relationship("Question", backref="notifications", lazy=True)

    # Entry creation date (to keep track)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Notification({self.id}, {self.user_id}, {self.message})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        link = None

        if self.question_id:
            if self.question.visible:
                link = url_for(
                    "frontend.question.fetch_question", id_question=self.question_id
                )
        elif self.link:
            link = self.link

        return {
            "id": self.id,
            "user_id": self.user_id,
            "message": self.message,
            "link": link,
            "type": self.type,
            "created_at": int(self.created_at.strftime("%Y%m%d%H%M%S")),
        }

    @staticmethod
    def validator(_mapper, connection, target):
        """Validate notification data, ensuring type is valid and required fields are present."""
        notification_type = connection.execute(
            db.select(NotificationType).filter_by(value=target.type)
        ).fetchone()

        if not notification_type:
            raise ValueError("NOTIFICATION MODEL: Notification type is invalid.")

        if notification_type.question_required and target.question_id is None:
            raise ValueError(
                f'NOTIFICATION MODEL: Notification type requires a question ("{target.type}").'
            )


# Attach event listeners
event.listen(Notification, "before_insert", Notification.validator)
event.listen(Notification, "before_update", Notification.validator)
