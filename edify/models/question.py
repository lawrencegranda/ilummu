"""Question-related models."""

# Standard Library imports
from datetime import datetime
from typing import Dict, Any

# Third-Party Framework imports
from sqlalchemy import Index, event

# Local Application imports
from edify.core import db
from edify.models.base import BaseModel
from edify.utils.constants import PREVIEW_LENGTH
from edify.utils.utils import (
    date_to_int,
    get_time_ago,
    get_seconds_ago,
    trim_text,
    format_text_to_html,
)


class Question(BaseModel):
    """
    Table that contains question information

    Entries are created when a user posts a question.
    Entries are updated when the question status changes or details are edited.
    """

    __table_args__ = (
        Index("ix_question_user_id", "user_id"),
        Index("ix_question_course_id", "course_id"),
    )

    # Primary key that identifies the question
    id = db.Column(db.Integer, primary_key=True)

    # User who posted the question
    # Many-to-One relationship with User model
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref="questions", lazy=True)

    # Course of the question
    # Many-to-One relationship with Course model
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    course = db.relationship("Course", backref="questions", lazy=True)

    # Detailed request for help
    request = db.Column(db.Text, nullable=False)

    # Time required to solve the question
    solve_time = db.Column(
        db.Integer, db.ForeignKey("time_interval.value"), nullable=False
    )
    time_interval = db.relationship("TimeInterval", lazy=True)

    # Price offered for solving the question
    price = db.Column(db.Float, nullable=False)

    # Original price offered for solving the question (might change)
    original_price = db.Column(
        db.Float, nullable=False, default=lambda c: c.get_current_parameters()["price"]
    )

    # Preferred method of communication
    method_id = db.Column(db.Integer, db.ForeignKey("method.id"), nullable=False)
    method = db.relationship("Method", backref="questions", lazy=True)

    # Indicates if the question has been solved
    solved = db.Column(db.Boolean, nullable=False, default=False)

    # Indicates if the question is visible or hidden
    visible = db.Column(db.Boolean, nullable=False, default=True)

    # Entry creation date (to keep track)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Entry updated date (to keep track)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Image url for the file
    image_url = db.Column(db.String(255), nullable=True)

    @property
    def request_html(self):
        """Get HTML formatted version of the request text."""
        return format_text_to_html(self.request)

    def __repr__(self):
        return f"Question({self.id}, {self.user_id}, {self.course_id}, {self.solved})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "request": self.request,
            "request_html": self.request_html,
            "solve_time_min": self.solve_time,
            "price": self.price,
            "method_id": self.method_id,
            "solved": self.solved,
            "created_at": date_to_int(self.created_at),
            "updated_at": date_to_int(self.updated_at),
            "image_url": self.image_url,
        }

        if not simplified:
            result["user"] = self.user.to_dict(simplified=False)
            result["subject"] = self.course.academic_field.name
            result["subject_code"] = self.course.academic_field.value
            result["course_code"] = self.course.code
            result["course_name"] = self.course.name
            result["time_ago"] = get_time_ago(self.created_at)
            result["seconds_ago"] = get_seconds_ago(self.updated_at)
            result["method"] = self.method.name
            result["method_value"] = self.method.value
            result["preview"] = trim_text(self.request, PREVIEW_LENGTH)
            result["solve_time"] = self.time_interval.shortname
            result["academic_field"] = self.course.academic_field.value
            result["original_price"] = self.original_price

        return result

    @staticmethod
    def validator(_mapper, _connection, target):
        """Validate question data before insert/update."""
        if target.price < 0:
            raise ValueError(
                f'QUESTION MODEL: Price must be a non-negative value ("{target.price}").'
            )

        if target.original_price and target.price < target.original_price:
            raise ValueError(
                f'QUESTION MODEL: Price ("{target.price}") must greater than the '
                f'original price ("{target.original_price}").'
            )

        if target.updated_at and target.updated_at < target.created_at:
            raise ValueError(
                f'QUESTION MODEL: Creation ("{target.created_at}") must be'
                f'before update ("{target.updated_at}").'
            )

        if target.solve_time <= 0:
            raise ValueError(
                f'QUESTION MODEL: Solve time must be a positive integer ("{target.solve_time}").'
            )


# Attach event listeners
event.listen(Question, "before_insert", Question.validator)
event.listen(Question, "before_update", Question.validator)


class Method(BaseModel):
    """
    Table that contains method information

    Entries are created to list available communication methods.
    """

    __table_args__ = (Index("ix_method_value", "value"),)

    # Primary key that identifies the method
    id = db.Column(db.Integer, primary_key=True)

    # Method value (e.g., method code)
    value = db.Column(db.String(20), unique=True, nullable=False)

    # Method name
    name = db.Column(db.String(100), nullable=False)

    # Whether the method is still supported
    supported = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"Method({self.id}, {self.name})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        return {
            "id": self.id,
            "value": self.value,
            "name": self.name,
        }


class TimeInterval(BaseModel):
    """
    Table that contains time interval information

    Entries are created to list available time intervals.
    """

    # Time interval value (in minutes)
    value = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)

    # Time interval name
    name = db.Column(db.String(100), nullable=False)

    # Short name for the time interval
    shortname = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"TimeInterval({self.value})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        return {
            "value": self.value,
            "name": self.name,
            "shortname": self.shortname,
        }
