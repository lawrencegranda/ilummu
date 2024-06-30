from edify import db, jwt
from edify.utils.constants import (
    AuthLevel,
    SupportedLanguages,
    OfferStatus,
)
from sqlalchemy import Index, Enum, event
from flask_login import UserMixin
from flask_jwt_extended import current_user, create_access_token, decode_token
from datetime import datetime, timedelta
from flask import current_app, jsonify
from collections import OrderedDict, defaultdict
from functools import wraps
from http import HTTPStatus
from typing import Optional, Dict, Any
import re


class User(db.Model, UserMixin):
    """
    Table that contains user information

    Inherits from `UserMixin` to provide default implementations for
    the required attributes and methods by Flask-Login extension:
    - is_authenticated: Returns True if the user has provided valid credentials.
    - is_active: Returns True if the user account is active.
    - is_anonymous: Returns True if the current user is an anonymous guest.
    - get_id(): Returns a unique identifier for the user.

    Entries are created in the sign up route
    Entries are updated in the account editing route
    """

    __table_args__ = (Index("ix_username", "username"),)

    # Primary key that identifies the user
    id = db.Column(db.Integer, primary_key=True)

    # User's username
    username = db.Column(db.String(30), unique=True, nullable=False)

    # User's first name
    firstname = db.Column(db.String(20), nullable=False)

    # User's last name
    lastname = db.Column(db.String(35), nullable=False)

    # User's school/university
    # Many-to-One relationship with School model
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), nullable=False)
    school = db.relationship("School", backref="users", lazy=True)

    # User's major
    # Many-to-One relationship with School model
    major_id = db.Column(db.Integer, db.ForeignKey("major.id"), nullable=False)
    major = db.relationship("Major", backref="users", lazy=True)

    # User's graduation year
    graduation = db.Column(db.DateTime, nullable=False)

    # User's email
    # Must be unique
    email = db.Column(db.String(120), unique=True, nullable=False)

    # User's phone number
    # Must be unique
    phone = db.Column(db.String(50), unique=True, nullable=False)

    # Account password
    # Must be hashed
    password = db.Column(db.String(90), nullable=False)

    # Entry creation date (to keep track)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Entry updated date (to keep track)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # API authentication token, token is given to user upon login to authenticate future requests
    # This is part of the API token-based authentication schema
    token = db.Column(db.String(300), nullable=True)

    token_last_refresh = db.Column(db.DateTime, nullable=True)

    # Field that indicates the level of permissions.
    auth_level = db.Column(Enum(AuthLevel), nullable=False, default=AuthLevel.STUDENT)

    # Whether or not the user verified it's email. NOT IMPLEMENTED
    mail_is_verified = db.Column(db.Boolean, nullable=False, default=False)

    # Whether or not the user verified it's phone number. NOT IMPLEMENTED
    phone_is_verified = db.Column(db.Boolean, nullable=False, default=False)

    # Indicates whether the user is a mock user or not.
    is_mock = db.Column(db.Boolean, nullable=False, default=False)

    # Preferred language by the user for display.
    language = db.Column(
        Enum(SupportedLanguages), nullable=False, default=SupportedLanguages.ENGLISH
    )

    # Profile picture
    image_file = db.Column(db.String(40), nullable=False, default="default.jpg")

    def get_reset_token(self, expires_sec=18000):
        return create_access_token(
            identity=self.id, expires_delta=timedelta(seconds=expires_sec)
        )

    @staticmethod
    def verify_reset_token(token):
        try:
            user_id = decode_token(token)["sub"]
        except Exception:
            return None
        return User.query.get(user_id)

    def generate_auth_token(self, expires_sec=1000):
        s = Serializer(current_app.config["SECRET_KEY"], expires_sec=expires_sec)
        return s.dumps({"id": self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except Exception:
            return None  # valid token, but expired or invalid token
        user = User.query.get(data["id"])
        return user

    def __repr__(self):
        return f"({self.id}, {self.username}, {self.email}\n"

    def to_dict(
        self,
        simplified=False,
    ) -> Dict[str, Any]:
        return_dict = {
            "id": self.id,
            "username": self.username,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "email": self.email,
            "phone": self.phone,
            "school": self.school,
            "major": self.major,
            "language": self.language,
        }

        # Add all extra information
        if not simplified:
            return_dict["auth_level"] = self.auth_level
            return_dict["mail_is_verified"] = self.mail_is_verified
            return_dict["phone_is_verified"] = self.phone_is_verified
            return_dict["is_mock"] = self.is_mock

        return return_dict

    @staticmethod
    def validator(mapper, connection, target):
        phone_regex = re.compile(r"^\+\d{1,2}\s\d{9,15}$")
        if not phone_regex.match(target.phone):
            raise ValueError(
                f'USER MODEL: Invalid phone number format ("{target.phone}").'
            )

        email_regex = re.compile(r"^[\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}$")
        if not email_regex.match(target.email):
            raise ValueError(f'USER MODEL: Invalid email format ("{target.email}").')

        if target.updated_at and target.updated_at < target.created_at:
            raise ValueError(
                f'USER MODEL: Creation ("{target.created_at}") must be before update ("{target.updated_at}").'
            )

        return


# Attach event listeners
event.listen(User, "before_insert", User.validator)
event.listen(User, "before_update", User.validator)


class Question(db.Model):
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

    # Price offered for solving the question
    price = db.Column(db.Float, nullable=False)

    # Original price offered for solving the question (might change)
    original_price = db.Column(
        db.Float, nullable=False, default=lambda c: c.get_current_parameters()["price"]
    )

    # Preferred method of communication
    method_id = db.Column(db.Integer, db.ForeignKey("method.id"), nullable=False)

    # Indicates if the question has been solved
    solved = db.Column(db.Boolean, nullable=False, default=False)

    # Indicates if the question is visible or hidden
    visible = db.Column(db.Boolean, nullable=False, default=True)

    # Entry creation date (to keep track)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Entry updated date (to keep track)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Question({self.id}, {self.user_id}, {self.course_id}, {self.solved})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "request": self.request,
            "solve_time": self.solve_time,
            "price": self.price,
            "method_id": self.method_id,
            "solved": self.solved,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def validator(mapper, connection, target):
        if target.price < 0:
            raise ValueError(
                f'QUESTION MODEL: Price must be a non-negative value ("{target.price}").'
            )

        if target.original_price and target.price < target.original_price:
            raise ValueError(
                f'QUESTION MODEL: Price ("{target.price}") must greater than the original price ("{target.original_price}").'
            )

        if target.updated_at and target.updated_at < target.created_at:
            raise ValueError(
                f'QUESTION MODEL: Creation ("{target.created_at}") must be before update ("{target.updated_at}").'
            )

        if target.solve_time <= 0:
            raise ValueError(
                f'QUESTION MODEL: Solve time must be a positive integer ("{target.solve_time}").'
            )

        return


# Attach event listeners
event.listen(Question, "before_insert", Question.validator)
event.listen(Question, "before_update", Question.validator)


class Offer(db.Model):
    """
    Table that contains offer information

    Entries are created when a user offers to help solve a question.
    Entries are updated when the offer status changes.
    """

    __table_args__ = (
        Index("ix_offer_question_id", "question_id"),
        Index("ix_offer_user_id", "user_id"),
    )

    # Primary key that identifies the offer
    id = db.Column(db.Integer, primary_key=True)

    # User who made the offer
    # Many-to-One relationship with User model
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref="offers", lazy=True)

    # Question associated with the offer
    # Many-to-One relationship with Question model
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    question = db.relationship("Question", backref="offers", lazy=True)

    # Amount offered
    amount = db.Column(db.Float, nullable=False)

    # Status of the offer
    status = db.Column(db.Enum(OfferStatus), nullable=False, default=OfferStatus.SENT)

    # Entry creation date (to keep track)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Entry updated date (to keep track)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Offer({self.id}, {self.question_id}, {self.amount}, {self.status})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question_id": self.question_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def validator(mapper, connection, target):
        if target.amount <= 0:
            raise ValueError(
                f'OFFER MODEL: Amount must be a positive value ("{target.amount}").'
            )

        if target.updated_at and target.updated_at < target.created_at:
            raise ValueError(
                f'OFFER MODEL: Creation ("{target.created_at}") must be before update ("{target.updated_at}").'
            )

        return


# Attach event listeners
event.listen(Offer, "before_insert", Offer.validator)
event.listen(Offer, "before_update", Offer.validator)


class Notification(db.Model):
    """
    Table that contains notification information

    Entries are created when a user needs to be notified.
    """

    __table_args__ = (
        Index("ix_notification_user_id", "user_id"),
        Index("ix_notification_type_id", "type_id"),
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
    type_id = db.Column(
        db.Integer, db.ForeignKey("notification_type.id"), nullable=False
    )

    # Link to further details
    link = db.Column(db.String(300), nullable=True)

    # Question it relates to, if it does
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=True)

    # Entry creation date (to keep track)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Notification({self.id}, {self.user_id}, {self.message})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "message": self.message,
            "link": self.link,
            "kind": self.type_id,
            "created_at": self.created_at,
        }

    @staticmethod
    def validator(mapper, connection, target):
        notification_type = connection.execute(
            db.select(NotificationType).filter_by(id=target.type_id)
        ).fetchone()

        if notification_type.question_required and target.question_id is None:
            raise ValueError(
                f'NOTIFICATION MODEL: Notification type requires a question ("{target.type_id}").'
            )

        return


# Attach event listeners
event.listen(Notification, "before_insert", Notification.validator)
event.listen(Notification, "before_update", Notification.validator)


class Major(db.Model):
    """
    Table that contains major information

    Entries are created to list available majors.
    """

    __table_args__ = (Index("ix_major_academic_field_id", "academic_field_id"),)

    # Primary key that identifies the major
    id = db.Column(db.Integer, primary_key=True)

    # Major name
    name = db.Column(db.String(100), nullable=False)

    # AcademicField associated with the major
    # Many-to-One relationship with AcademicField model
    academic_field_id = db.Column(
        db.Integer, db.ForeignKey("academic_field.id"), nullable=False
    )
    academic_field = db.relationship("AcademicField", backref="majors", lazy=True)

    # School associated with the major
    # Many-to-One relationship with School model
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), nullable=False)
    school = db.relationship("School", backref="majors", lazy=True)

    def __repr__(self):
        return f"Major({self.id}, {self.name})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "academic_field_id": self.academic_field_id,
            "school_id": self.school_id,
        }

    @staticmethod
    def validator(mapper, connection, target):
        academic_field = connection.execute(
            db.select(AcademicField).filter_by(id=target.academic_field_id)
        ).fetchone()

        if academic_field.school_id != target.school_id:
            raise ValueError(
                f'MAJOR MODEL: School ("{target.school_id}") is inconsistent with the academic field\'s school ("{target.academic_field.school_id}").'
            )

        return


# Attach event listeners
event.listen(Major, "before_insert", Major.validator)
event.listen(Major, "before_update", Major.validator)


class AcademicField(db.Model):
    """
    Table that contains academic_field information

    Entries are created to list available academic_fields.
    """

    __table_args__ = (Index("ix_academic_field_school_id", "school_id"),)

    # Primary key that identifies the academic_field
    id = db.Column(db.Integer, primary_key=True)

    # AcademicField's value (e.g., academic_field code)
    value = db.Column(db.String(20), unique=True, nullable=False)

    # AcademicField's name
    name = db.Column(db.String(100), nullable=False)

    # AcademicField's school
    # Many-to-One relationship with School model
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), nullable=False)
    school = db.relationship("School", backref="academic_fields", lazy=True)

    def __repr__(self):
        return f"AcademicField({self.id}, {self.name}, {self.school_id})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "value": self.value,
            "name": self.name,
            "school_id": self.school_id,
        }


class Method(db.Model):
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

    def __repr__(self):
        return f"Method({self.id}, {self.name})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "value": self.value,
            "name": self.name,
        }


class TimeInterval(db.Model):
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "name": self.name,
            "shortname": self.shortname,
        }


class Course(db.Model):
    """
    Table that contains course information

    Entries are created to list available courses.
    """

    __table_args__ = (
        Index("ix_course_code", "code"),
        Index("ix_course_academic_field_id", "academic_field_id"),
    )

    # Primary key that identifies the course
    id = db.Column(db.Integer, primary_key=True)

    # Course value (e.g., course code)
    code = db.Column(db.String(10), nullable=False)

    # Course name
    name = db.Column(db.String(100), nullable=False)

    # AcademicField associated with the course
    # Many-to-One relationship with AcademicField model
    academic_field_id = db.Column(
        db.Integer, db.ForeignKey("academic_field.id"), nullable=False
    )
    academic_field = db.relationship("AcademicField", backref="courses", lazy=True)

    # University associated with the course
    # Many-to-One relationship with AcademicField model
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), nullable=False)
    school = db.relationship("School", backref="courses", lazy=True)

    def __repr__(self):
        return f"Course({self.id}, {self.code}, {self.name}, {self.academic_field_id})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "academic_field_id": self.academic_field_id,
            "school_id": self.school_id,
        }

    @staticmethod
    def validator(mapper, connection, target):
        academic_field = connection.execute(
            db.select(AcademicField).filter_by(id=target.academic_field_id)
        ).fetchone()

        if academic_field.school_id != target.school_id:
            raise ValueError(
                f'COURSE MODEL: School ("{target.school_id}") is inconsistent with the academic field\'s school ("{target.academic_field.school_id}").'
            )

        return


# Attach event listeners
event.listen(Course, "before_insert", Course.validator)
event.listen(Course, "before_update", Course.validator)


class School(db.Model):
    """
    Table that contains school information

    Entries are created to list available schools.
    """

    __table_args__ = (Index("ix_school_name", "name"),)

    # Primary key that identifies the school
    id = db.Column(db.Integer, primary_key=True)

    # School name
    name = db.Column(db.String(100), nullable=False, unique=True)

    # School country
    country = db.Column(db.String(100), nullable=True)

    # School state
    state = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"School({self.id}, {self.name})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "state": self.state,
        }


class NotificationType(db.Model):
    """
    Table that contains notification type information

    Entries are created to list available notification types.
    """

    __table_args__ = (Index("ix_notification_name", "name"),)

    # Primary key that identifies the notification type
    id = db.Column(db.Integer, primary_key=True)

    # Notification type name
    name = db.Column(db.String(100), nullable=False, unique=True)

    # Whether the type requires a link to a question.
    question_required = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"NotificationType({self.id}, {self.name})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "question_required": self.question_required,
        }
