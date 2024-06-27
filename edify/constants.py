from enum import Enum


class AuthLevel(Enum):
    """Authorization levels"""

    # Simple student: Basic access level for students
    STUDENT = 0

    # School Admin: High-level admin with broad oversight capabilities within a school
    SCHOOL_ADMIN = 5

    # Super Admin: Root account with the highest level of access
    # Can see/edit everything
    SUPER_ADMIN = 100


class EdifyEnvironments(Enum):
    """Deployment environments for the application"""

    # Production environment
    PRODUCTION = "PRODUCTION"

    # Local development environment
    LOCAL = "LOCAL"

    # Test environment
    TEST = "TEST"


class SupportedLanguages(Enum):
    """List of languages supported by the platform."""

    # Options must be one of:
    # https://meta.wikimedia.org/wiki/Template:List_of_language_names_ordered_by_code?setlang=ru

    # English language support
    ENGLISH = "en"


class OfferStatus(Enum):
    """List of status for a question."""

    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EDITED = "EDITED"
    REMOVED = "REMOVED"
