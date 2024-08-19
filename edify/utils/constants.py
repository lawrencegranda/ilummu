# Standard Library imports
from enum import Enum
from http import HTTPStatus
from typing import List, Tuple

# Third-Party Framework imports
from webargs import fields, validate


# Number of characters to show in the question request preview.
PREVIEW_LENGTH: int = 127


class ErrorType(Enum):
    """Different Error Types"""

    USER_NOT_AUTHENTICATED = HTTPStatus.UNAUTHORIZED
    USER_NOT_VERIFIED = HTTPStatus.UNAUTHORIZED
    INCORRECT_CREDENTIALS = HTTPStatus.UNAUTHORIZED
    ACCESS_FORBIDDEN = HTTPStatus.FORBIDDEN
    MAINTENANCE = HTTPStatus.FORBIDDEN
    BAD_REQUEST = HTTPStatus.BAD_REQUEST
    REQUEST_TIMEOUT = HTTPStatus.REQUEST_TIMEOUT
    INTERNAL_ERROR = HTTPStatus.INTERNAL_SERVER_ERROR
    NOT_FOUND = HTTPStatus.NOT_FOUND
    USER_NOT_FOUND = HTTPStatus.NOT_FOUND
    UNAUTHORIZED = HTTPStatus.UNAUTHORIZED
    NOT_IMPLEMENTED = HTTPStatus.NOT_IMPLEMENTED


class EdifyEnvironments(Enum):
    """Deployment environments for the application"""

    # Production environment
    PRODUCTION = "PRODUCTION"

    # Local development environment
    LOCAL = "LOCAL"

    # Test environment
    TEST = "TEST"


class EnumBase:
    @classmethod
    def keys(cls) -> List[str]:
        """Returns a list of all the keys in the Enum class."""
        return [
            key
            for key, value in vars(cls).items()
            if not key.startswith("_") and key == key.upper()
        ]

    @classmethod
    def values(cls) -> List[str]:
        """Returns a list of all the values in the Enum class."""
        return [
            value
            for key, value in vars(cls).items()
            if not key.startswith("_") and key == key.upper()
        ]

    @classmethod
    def items(cls) -> List[Tuple[str, str]]:
        """Returns a list of all the key-value pairs in the Enum class."""
        return [
            (key, value)
            for key, value in vars(cls).items()
            if not key.startswith("_") and key == key.upper()
        ]


class AuthLevelEnum(EnumBase):
    """Authorization levels"""

    # Simple student: Basic access level for students
    STUDENT = "STUDENT"

    # School Admin: High-level admin with broad oversight capabilities within a school
    SCHOOL_ADMIN = "SCHOOL_ADMIN"

    # Super Admin: Root account with the highest level of access
    # Can see/edit everything
    SUPER_ADMIN = "SUPER_ADMIN"


class SupportedLanguagesEnum(EnumBase):
    """List of languages supported by the platform."""

    # English language support
    ENGLISH = "ENGLISH"


class OfferStatusEnum(EnumBase):
    """List of status for an offer question."""

    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EDITED = "EDITED"
    REMOVED = "REMOVED"

    inactive = [REMOVED]


class NotificationTypeEnum(EnumBase):
    """List of notification types."""

    GENERAL = "GENERAL"
    OFFER_ACCEPTED = "OFFER_ACCEPTED"
    OFFER_DECLINED = "OFFER_DECLINED"
    NEW_OFFER = "NEW_OFFER"
    UPDATED_OFFER = "UPDATED_OFFER"
    PRICE_CHANGE = "PRICE_CHANGE"
    QUESTION_SOLVED = "QUESTION_SOLVED"
    ACCOUNT_VERIFIED = "ACCOUNT_VERIFIED"
    PASSWORD_RESET = "PASSWORD_RESET"
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    QUESTION_CREATED = "QUESTION_CREATED"
    QUESTION_DELETED = "QUESTION_DELETED"
    QUESTION_UPDATED = "QUESTION_UPDATED"

    # Metadata to store additional information
    question_required = {
        "GENERAL": False,
        "OFFER_ACCEPTED": True,
        "OFFER_DECLINED": True,
        "NEW_OFFER": True,
        "UPDATED_OFFER": True,
        "PRICE_CHANGE": True,
        "QUESTION_SOLVED": True,
        "ACCOUNT_VERIFIED": False,
        "PASSWORD_RESET": False,
        "ACCOUNT_CREATED": False,
        "QUESTION_CREATED": True,
        "QUESTION_DELETED": True,
        "QUESTION_UPDATED": True,
    }

    @classmethod
    def requires_question(cls, notification_type: str) -> bool:
        """
        Determines whether a given notification type requires a question.

        Args:
            notification_type (str): The type of notification to check.

        Raises:
            ValueError: If the provided notification_type is not valid.

        Returns:
            bool: True if the notification type requires a question, False otherwise.
        """

        if (
            notification_type in cls.keys()
            and notification_type in cls.question_required.keys()
        ):
            return cls.question_required[notification_type]
        raise ValueError(f"{notification_type} is not a valid notification type.")


QuestionSchema = {
    "class_code": fields.Str(required=True, validate=validate.Length(min=4)),
    "class_name": fields.Str(required=True, validate=validate.Length(min=1)),
    "academic_field": fields.Str(required=True, validate=validate.Length(min=1)),
    "method": fields.Str(required=True),
    "solve_time": fields.Int(required=True, validate=validate.Range(min=1)),
    "price": fields.Float(required=True, validate=validate.Range(min=0)),
    "request_message": fields.Str(required=True, validate=validate.Length(min=1)),
}
