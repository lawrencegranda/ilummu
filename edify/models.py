# Standard Library imports
from abc import ABCMeta, ABC, abstractmethod
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta, timezone
from functools import wraps
from http import HTTPStatus
import json
from typing import Optional, Dict, Any, List
import random

# Third-Party Framework imports
from flask import current_app, jsonify, url_for, session
from flask_jwt_extended import create_access_token, decode_token, create_refresh_token
from flask_login import UserMixin
from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous.exc import BadSignature, SignatureExpired
from sqlalchemy import Index, UniqueConstraint, event
from sqlalchemy.orm import Session
from sqlalchemy import func

# Local Application imports
from edify import db, jwt, bcrypt
from edify.utils.constants import (
    AuthLevelEnum,
    NotificationTypeEnum,
    OfferStatusEnum,
    PREVIEW_LENGTH,
    SupportedLanguagesEnum,
)
from edify.utils.utils import (
    date_to_int,
    format_lower_case,
    format_phone,
    format_title_case,
    format_upper_case,
    get_college_year,
    get_time_ago,
    get_seconds_ago,
    trim_text,
    validate_email,
    validate_email_postfix,
    validate_phone,
    validate_auth_data,
)


# Custom metaclass combining the metaclasses of SQLAlchemy's Model and ABCMeta
class ModelABCMeta(type(db.Model), ABCMeta):
    pass


class BaseModel(db.Model, ABC, metaclass=ModelABCMeta):
    """
    Abstract base class for all models, providing common methods and enforcing
    implementation of essential methods in subclasses.
    """

    __abstract__ = True

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def to_dict(self, simplified=False) -> Dict[str, Any]:
        pass

    @staticmethod
    def to_dict_all(elem_list: List["BaseModel"]) -> List[Dict[str, Any]]:
        return [elem.to_dict(simplified=False) for elem in elem_list]


# Custom metaclass combining the metaclasses of SQLAlchemy's Model and ABCMeta
class UserModelABCMeta(type(BaseModel), type(UserMixin)):
    pass


class User(BaseModel, UserMixin, metaclass=UserModelABCMeta):
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

    __table_args__ = (
        Index("ix_username", "username"),
        Index("ix_email", "email"),
        Index("ix_phone", "phone"),
    )

    # Primary key that identifies the user
    id = db.Column(db.Integer, primary_key=True)

    # User's username
    username = db.Column(db.String(30), unique=True, nullable=False)

    # User's first name, titlecase
    firstname = db.Column(db.String(20), nullable=False)

    # User's last name, titlecase
    lastname = db.Column(db.String(35), nullable=False)

    # User's email, lowercase
    # Must be unique
    email = db.Column(db.String(120), unique=True, nullable=False)

    # User's phone number
    # Must be unique
    phone = db.Column(db.String(50), unique=True, nullable=False)

    # Account password
    # Must be hashed
    password = db.Column(db.String(90), nullable=False)

    # User's school/university
    # Many-to-One relationship with School model
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), nullable=False)
    school = db.relationship("School", backref="users", lazy=True)

    # User's major
    # Many-to-One relationship with School model
    major_id = db.Column(db.Integer, db.ForeignKey("major.id"), nullable=False)
    major = db.relationship("Major", backref="users", lazy=True)

    # Rating
    rating = db.Column(db.Float, nullable=True)

    # User's graduation year
    graduation = db.Column(db.DateTime, nullable=False)

    # Entry creation date (to keep track)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Entry updated date (to keep track)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Password last reset date (to keep track)
    password_last_reset = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )

    # Field that indicates the level of permissions.
    auth_level = db.Column(
        db.String(30),
        db.ForeignKey("auth_level.value"),
        nullable=False,
        default=AuthLevelEnum.STUDENT,
    )

    # Whether or not the user verified it's email. NOT IMPLEMENTED
    mail_is_verified = db.Column(db.Boolean, nullable=False, default=False)

    # Whether or not the user verified it's phone number. NOT IMPLEMENTED
    phone_is_verified = db.Column(db.Boolean, nullable=False, default=False)

    # Indicates whether the user is a mock user or not.
    is_mock = db.Column(db.Boolean, nullable=False, default=False)

    # Indicates whether the user is test user or not.
    is_test = db.Column(db.Boolean, nullable=False, default=False)

    # Preferred language by the user for display.
    language = db.Column(
        db.String(30),
        db.ForeignKey("supported_language.value"),
        nullable=False,
        default=SupportedLanguagesEnum.ENGLISH,
    )

    # Profile picture
    image_file = db.Column(db.String(40), nullable=False, default="default.jpg")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password, password)

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.generate_password_hash(password).decode("utf-8")

    def get_access_token(self) -> Any:
        """
        Generate an access token for the user and update the user's token information.

        Args:
            user (User): The user for whom the access token is generated.

        Returns:
            str: The generated access token.
        """
        access_token = create_access_token(identity=self.id)

        return access_token

    def get_refresh_token(self) -> Any:
        return create_refresh_token(identity=self.id)

    def generate_reset_token(self):
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

        return serializer.dumps((self.id, self.password_last_reset.timestamp()))

    @staticmethod
    def validate_reset_token(token: str):
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            user_id, password_last_reset = serializer.loads(
                token,
                max_age=current_app.config["RESET_PASS_TOKEN_MAX_AGE"],
            )
        except (BadSignature, SignatureExpired):
            return None

        user = db.session.get(User, user_id)

        if user.password_last_reset.timestamp() != password_last_reset:
            return None

        return user

    def generate_session_auth_code(self):
        # Retrieve the stored code and timestamp from the session
        auth = session.get("auth")

        # Check if the data is stored in the session
        if auth:
            del session["auth"]

        # Generate a random 6-digit code
        auth_code = random.randint(100000, 999999)

        current_time = datetime.now(timezone.utc)
        expiration_time = current_time + timedelta(
            seconds=current_app.config["AUTH_TOKEN_MAX_AGE"]
        )

        # Store the code in the session with ISO 8601 formatted datetime strings
        session["auth"] = {
            "code": auth_code,
            "id": self.id,
            "issued": current_time.isoformat(),
            "expiration": expiration_time.isoformat(),
        }

        assert validate_auth_data(session["auth"])

        return auth_code

    def validate_session_auth_code(self, input_code: int):
        # Retrieve the stored code and timestamp from the session
        auth = session.get("auth")

        # Check if the data is stored in the session
        if not auth:
            return False

        # Check if the code is invalid or has expired
        if not validate_auth_data(auth) or datetime.now(
            timezone.utc
        ) > datetime.fromisoformat(auth["expiration"]):
            del session["auth"]
            return False

        # Check if the input code matches the stored code
        if str(auth["code"]) != str(input_code):
            return False

        # Check the identity
        if auth["id"] != self.id:
            del session["auth"]
            return False

        return True

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
            "school_id": self.school_id,
            "major_id": self.major_id,
            "language": self.language,
            "graduation": self.graduation,
        }

        # Add all extra information
        if not simplified:
            return_dict["auth_level"] = self.auth_level
            return_dict["mail_is_verified"] = self.mail_is_verified
            return_dict["phone_is_verified"] = self.phone_is_verified
            return_dict["is_mock"] = self.is_mock
            return_dict["year"] = get_college_year(self.graduation)
            return_dict["major"] = self.major.name
            return_dict["rating"] = self.rating
            return_dict["notifications"] = Notification.to_dict_all(self.notifications)

        return return_dict

    @staticmethod
    def validator(mapper, connection, target):
        if not validate_phone(target.phone):
            raise ValueError(
                f'USER MODEL: Invalid phone number format ("{target.phone}").'
            )

        if not validate_email(target.email):
            raise ValueError(f'USER MODEL: Invalid email format ("{target.email}").')

        if target.updated_at and target.updated_at < target.created_at:
            raise ValueError(
                f'USER MODEL: Creation ("{target.created_at}") must be before update ("{target.updated_at}").'
            )

        return

    @staticmethod
    def format_phone(target, value, oldvalue, initiator):
        return format_phone(value)


# Attach event listeners
event.listen(User, "before_insert", User.validator)
event.listen(User, "before_update", User.validator)
event.listen(User.phone, "set", User.format_phone, retval=True)
event.listen(User.firstname, "set", format_title_case, retval=True)
event.listen(User.lastname, "set", format_title_case, retval=True)
event.listen(User.email, "set", format_lower_case, retval=True)


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

    def __repr__(self):
        return f"Question({self.id}, {self.user_id}, {self.course_id}, {self.solved})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "request": self.request,
            "solve_time_min": self.solve_time,
            "price": self.price,
            "method_id": self.method_id,
            "solved": self.solved,
            "created_at": date_to_int(self.created_at),
            "updated_at": date_to_int(self.updated_at),
        }

        if simplified == False:
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


class OfferStatus(BaseModel):
    """
    Table that stores the status of offers/questions.
    """

    value = db.Column(db.String(50), unique=True, nullable=False, primary_key=True)

    def __repr__(self):
        return f"OfferStatus({self.value})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        return {
            "value": self.value,
        }

    @staticmethod
    def validator(mapper, connection, target):
        if not target.value in OfferStatusEnum.values():
            raise ValueError(f'OFFER STATUS MODEL: Invalid value ("{target.value}").')


# Attach event listeners
event.listen(OfferStatus, "before_insert", OfferStatus.validator)
event.listen(OfferStatus, "before_update", OfferStatus.validator)


class Offer(BaseModel):
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

    # Whether the offer is active
    active = db.Column(db.Boolean, nullable=False, default=True)

    # Status of the offer
    status = db.Column(
        db.String(30),
        db.ForeignKey("offer_status.value"),
        nullable=False,
        default=OfferStatusEnum.SENT,
    )

    # Entry creation date (to keep track)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Entry updated date (to keep track)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Offer({self.id}, {self.question_id}, {self.amount}, {self.status}, {self.active})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "question_id": self.question_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "status": self.status,
            "active": self.active,
            "created_at": date_to_int(self.created_at),
            "updated_at": date_to_int(self.updated_at),
        }

        if simplified == False:
            result["user"] = self.user.to_dict(simplified=False)

        return result

    @staticmethod
    def validator(mapper, connection, target: "Offer"):
        # Fill in default values
        if target.active is None:
            target.active = True
        if target.status is None:
            target.status = OfferStatusEnum.SENT

        # Ensure amount is positive
        if target.amount <= 0:
            raise ValueError(
                f'OFFER MODEL: Amount must be a positive value ("{target.amount}").'
            )

        # Ensure created_at is before updated_at
        if target.updated_at and target.updated_at < target.created_at:
            raise ValueError(
                f'OFFER MODEL: Creation ("{target.created_at}") must be before update ("{target.updated_at}").'
            )

        # Enforce that if the offer is inactive, it cannot have an active status
        if target.status in OfferStatusEnum.inactive and target.active:
            raise ValueError(
                f'OFFER MODEL: Offer status is inactive ("{target.status}") but still active).'
            )

        # Enforce that if the offer is not active, it must have an inactive status
        if not target.active and not (target.status in OfferStatusEnum.inactive):
            raise ValueError(
                f'OFFER MODEL: Offer is not active but status is not inactive ("{target.status}").'
            )

        # Ensure only one active offer per user and question
        if target.active:
            session = Session.object_session(target)

            # Count the number of active offers for the same user_id and question_id, excluding the current offer
            active_offers_count = (
                session.query(func.count(Offer.id))
                .filter(
                    Offer.user_id == target.user_id,
                    Offer.question_id == target.question_id,
                    Offer.active == True,
                    Offer.id
                    != target.id,  # Exclude the current offer if it exists (on update)
                )
                .scalar()
            )

            if active_offers_count > 0:
                raise ValueError(
                    f"OFFER MODEL: Only one active offer per user and question is allowed. User: {target.user_id}, Question: {target.question_id}."
                )

        return


# Attach event listeners
event.listen(Offer, "before_insert", Offer.validator)
event.listen(Offer, "before_update", Offer.validator)


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
    def validator(mapper, connection, target):
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
    def validator(mapper, connection, target):
        notification_type = connection.execute(
            db.select(NotificationType).filter_by(value=target.type)
        ).fetchone()

        if not notification_type:
            raise ValueError(f"NOTIFICATION MODEL: Notification type is invalid.")

        if notification_type.question_required and target.question_id is None:
            raise ValueError(
                f'NOTIFICATION MODEL: Notification type requires a question ("{target.type}").'
            )

        return


# Attach event listeners
event.listen(Notification, "before_insert", Notification.validator)
event.listen(Notification, "before_update", Notification.validator)


class Major(BaseModel):
    """
    Table that contains major information

    Entries are created to list available majors.
    """

    __table_args__ = (
        Index("ix_major_academic_field_id", "academic_field_id"),
        UniqueConstraint("name", "academic_field_id", name="_major_field_uc"),
    )

    # Primary key that identifies the major
    id = db.Column(db.Integer, primary_key=True)

    # Major name, titlecase
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

    def to_dict(self, simplified=True) -> Dict[str, Any]:
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
event.listen(Major.name, "set", format_title_case, retval=True)


class AcademicField(BaseModel):
    """
    Table that contains academic_field information

    Entries are created to list available academic_fields.
    """

    __table_args__ = (
        Index("ix_academic_field_school_id", "school_id"),
        UniqueConstraint("name", "school_id", name="_field_school_uc"),
    )

    # Primary key that identifies the academic_field
    id = db.Column(db.Integer, primary_key=True)

    # AcademicField's value (e.g., academic_field code), lowercase
    value = db.Column(db.String(30), unique=True, nullable=False)

    # AcademicField's name, titlecase
    name = db.Column(db.String(100), nullable=False)

    # AcademicField's school
    # Many-to-One relationship with School model
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), nullable=False)
    school = db.relationship("School", backref="academic_fields", lazy=True)

    def __repr__(self):
        return f"AcademicField({self.id}, {self.name}, {self.school_id})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        return {
            "id": self.id,
            "value": self.value,
            "name": self.name,
            "school_id": self.school_id,
        }


# Attach event listeners
event.listen(AcademicField.value, "set", format_lower_case, retval=True)


class Course(BaseModel):
    """
    Table that contains course information

    Entries are created to list available courses.
    """

    __table_args__ = (
        Index("ix_course_code", "code"),
        Index("ix_course_academic_field_id", "academic_field_id"),
        UniqueConstraint("code", "name", "academic_field_id", name="_course_field_uc"),
    )

    # Primary key that identifies the course
    id = db.Column(db.Integer, primary_key=True)

    # Course value (e.g., course code), uppercase
    code = db.Column(db.String(10), nullable=False)

    # Course name, titlecase
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

    def to_dict(self, simplified=True) -> Dict[str, Any]:
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
event.listen(Course.code, "set", format_upper_case, retval=True)
event.listen(Course.name, "set", format_title_case, retval=True)


class School(BaseModel):
    """
    Table that contains school information

    Entries are created to list available schools.
    """

    __table_args__ = (Index("ix_school_name", "name"),)

    # Primary key that identifies the school
    id = db.Column(db.Integer, primary_key=True)

    # School name, titlecase
    name = db.Column(db.String(100), nullable=False, unique=True)

    # School country, titlecase
    country = db.Column(db.String(100), nullable=True)

    # School state, titlecase
    state = db.Column(db.String(100), nullable=True)

    # Enterprise email, ex.: cornell.edu, lowercase
    email_postfix = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"School({self.id}, {self.name}, {self.email_postfix})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "state": self.state,
            "email_postfix": self.email_postfix,
        }

    @staticmethod
    def validator(mapper, connection, target):
        if target.email_postfix and not validate_email_postfix(target.email_postfix):
            raise ValueError(
                f'SCHOOL MODEL: Email postfix does not fit pattern ("{target.email_postfix}").'
            )


# Attach event listeners
event.listen(School, "before_insert", School.validator)
event.listen(School, "before_update", School.validator)
event.listen(School.name, "set", format_title_case, retval=True)
event.listen(School.country, "set", format_title_case, retval=True)
event.listen(School.state, "set", format_title_case, retval=True)
event.listen(School.email_postfix, "set", format_lower_case, retval=True)


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


class AuthLevel(BaseModel):
    """
    Table that stores different authorization levels for users.
    """

    value = db.Column(db.String(50), unique=True, nullable=False, primary_key=True)

    def __repr__(self):
        return f"AuthLevel({self.value})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        return {
            "value": self.value,
        }

    @staticmethod
    def validator(mapper, connection, target):
        if not target.value in AuthLevelEnum.values():
            raise ValueError(f'AUTHLEVEL MODEL: Invalid value ("{target.value}").')


# Attach event listeners
event.listen(AuthLevel, "before_insert", AuthLevel.validator)
event.listen(AuthLevel, "before_update", AuthLevel.validator)


class SupportedLanguage(BaseModel):
    """
    Table that stores the languages supported by the platform.
    """

    value = db.Column(db.String(50), unique=True, nullable=False, primary_key=True)

    def __repr__(self):
        return f"SupportedLanguage({self.value})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        return {
            "value": self.value,
        }

    @staticmethod
    def validator(mapper, connection, target):
        if not target.value in SupportedLanguagesEnum.values():
            raise ValueError(
                f'SUPPORTED LANGUAGE MODEL: Invalid value ("{target.value}").'
            )


# Attach event listeners
event.listen(SupportedLanguage, "before_insert", SupportedLanguage.validator)
event.listen(SupportedLanguage, "before_update", SupportedLanguage.validator)
