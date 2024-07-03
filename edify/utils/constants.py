from enum import Enum
from http import HTTPStatus


class ErrorType(Enum):
    """Different Error Types"""

    # USER_NOT_AUTHENTICATED = "USER_NOT_AUTHENTICATED"
    # USER_NOT_VERIFIED = "USER_NOT_VERIFIED"
    # INCORRECT_CREDENTIALS = "INCORRECT_CREDENTIALS"
    # ACCESS_FORBIDDEN = "ACCESS_FORBIDDEN"
    # MAINTENANCE = "MAINTENANCE"

    USER_NOT_AUTHENTICATED = HTTPStatus.UNAUTHORIZED
    USER_NOT_VERIFIED = HTTPStatus.UNAUTHORIZED
    INCORRECT_CREDENTIALS = HTTPStatus.UNAUTHORIZED
    ACCESS_FORBIDDEN = HTTPStatus.FORBIDDEN
    MAINTENANCE = HTTPStatus.FORBIDDEN
    BAD_REQUEST = HTTPStatus.BAD_REQUEST
    REQUEST_TIMEOUT = HTTPStatus.REQUEST_TIMEOUT
    INTERNAL_ERROR = HTTPStatus.INTERNAL_SERVER_ERROR


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
    def values(cls):
        return [value for key, value in vars(cls).items() if not key.startswith("__")]


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
