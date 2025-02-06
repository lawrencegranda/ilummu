"""User-related models."""

# Standard Library imports
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import random

# Third-Party Framework imports
from flask import current_app, session
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_login import UserMixin
from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous.exc import BadSignature, SignatureExpired
from sqlalchemy import Index, event

# Local Application imports
from edify.core import db, bcrypt
from edify.models.base import BaseModel
from edify.models.notification import Notification
from edify.utils.constants import (
    AuthLevelEnum,
    SupportedLanguagesEnum,
)
from edify.utils.utils import (
    format_lower_case,
    format_phone,
    format_title_case,
    get_college_year,
    validate_email,
    validate_phone,
    validate_auth_data,
)


class User(BaseModel, UserMixin):
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
        """Verify if provided password matches the hashed password."""
        return bcrypt.check_password_hash(self.password, password)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password string using bcrypt."""
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
        """Generate and return a refresh token for user authentication."""
        return create_refresh_token(identity=self.id)

    def generate_reset_token(self):
        """Generate a secure token for password reset using app's secret key."""
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

        return serializer.dumps((self.id, self.password_last_reset.timestamp()))

    @staticmethod
    def validate_reset_token(token: str):
        """Validate a password reset token and return associated user if valid."""
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

    def generate_session_auth_code(self) -> int:
        """Generate and store a random 6-digit authentication code in the session."""
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

    def has_valid_session_auth_code(self) -> bool:
        """Check if user has a valid authentication code in their session."""
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

        # Check the identity
        if auth["id"] != self.id:
            del session["auth"]
            return False

        return True

    def sec_since_issued_auth_code(self) -> float:
        """Return number of seconds since the authentication code was issued."""
        # Check for valid code
        if not self.has_valid_session_auth_code():
            return -1

        # Retrieve the stored code
        auth = session.get("auth")

        # Parse the issued timestamp from ISO format
        issued_time = datetime.fromisoformat(auth["issued"])

        # Get the current time
        current_time = datetime.now(timezone.utc)

        # Calculate the difference in seconds
        time_diff = current_time - issued_time
        seconds_since_issued = time_diff.total_seconds()

        return seconds_since_issued

    def validate_session_auth_code(self, input_code: int) -> bool:
        """Validate if the provided code matches the stored authentication code."""
        # Check for valid code
        if not self.has_valid_session_auth_code():
            return False

        # Retrieve the stored code
        auth = session.get("auth")

        # Check if the input code matches the stored code
        if str(auth["code"]) != str(input_code):
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
    def validator(_mapper, _connection, target):
        """Validate user data before insert/update."""
        if not validate_phone(target.phone):
            raise ValueError(
                f'USER MODEL: Invalid phone number format ("{target.phone}").'
            )

        if not validate_email(target.email):
            raise ValueError(f'USER MODEL: Invalid email format ("{target.email}").')

        if target.updated_at and target.updated_at < target.created_at:
            raise ValueError(
                f'USER MODEL: Creation ("{target.created_at}") must be before '
                f'update ("{target.updated_at}").'
            )

    @staticmethod
    def format_phone(_target, value, _oldvalue, _initiator):
        """Format phone number to standardized format using format_phone utility."""
        return format_phone(value)


# Attach event listeners
event.listen(User, "before_insert", User.validator)
event.listen(User, "before_update", User.validator)
event.listen(User.phone, "set", User.format_phone, retval=True)
event.listen(User.firstname, "set", format_title_case, retval=True)
event.listen(User.lastname, "set", format_title_case, retval=True)
event.listen(User.email, "set", format_lower_case, retval=True)


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
    def validator(_mapper, _connection, target):
        """Validate auth level value before insert/update."""
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
    def validator(_mapper, _connection, target):
        """Validate supported language value before insert/update."""
        if not target.value in SupportedLanguagesEnum.values():
            raise ValueError(
                f'SUPPORTED LANGUAGE MODEL: Invalid value ("{target.value}").'
            )


# Attach event listeners
event.listen(SupportedLanguage, "before_insert", SupportedLanguage.validator)
event.listen(SupportedLanguage, "before_update", SupportedLanguage.validator)
