"""User-related utility functions for authentication and user management."""

# Standard Library imports
from typing import Optional, Tuple, Dict, Any

# Third-Party Framework imports
from flask import current_app, jsonify
from flask.typing import ResponseReturnValue
from flask_jwt_extended import current_user, set_access_cookies, set_refresh_cookies
from flask_login import UserMixin

# Local Application imports
from edify.core import db
from edify.models import User, Question, School, Major
from edify.utils.constants import (
    SupportedLanguagesEnum,
    ErrorType,
    NotificationTypeEnum,
)
from edify.utils.utils import (
    format_phone,
    error_response,
    validate_phone,
    validate_email,
    validate_password,
    generate_funny_username,
)

from edify.backend.utils import commit_changes, create_notification


def get_current_user() -> Optional[User]:
    """
    Helper function to get the current user.

    Returns:
        Optional[User]: The current user if authenticated, otherwise None.
    """
    return current_user if isinstance(current_user, UserMixin) else None


def generate_refresh_token(user: User) -> str:
    """
    Generate a refresh token for the user.

    Args:
        user (User): The user for whom the refresh token is generated.

    Returns:
        str: The generated refresh token.
    """
    refresh_token = user.get_refresh_token()
    return refresh_token


def check_author(id_user: int, id_question: int) -> bool:
    """
    Check if the user is the author of a specific question.

    Args:
        id_user (int): The ID of the user.
        id_question (int): The ID of the question to check.

    Returns:
        bool: Wheter the user is the author of that question
    """
    # Abort if the user is not found
    if not db.session.get(User, id_user):
        return False

    # Query the Question model to find the question by its ID
    question = db.session.get(Question, id_question)

    # Abort if the question does not exist
    if not question:
        return False

    # Check if user_id's match
    return id_user == question.user_id


# pylint: disable=too-many-return-statements
def validate_signup_data(
    args: dict, is_google_account: bool = False
) -> Optional[ResponseReturnValue]:
    """Validate signup form data."""

    # Validate phone
    if not validate_phone(args["phone"]):
        return error_response(
            f"Invalid phone format {args['phone']}", ErrorType.BAD_REQUEST
        )

    # Validate email
    if not validate_email(args["email"]):
        return error_response("Invalid email format.", ErrorType.BAD_REQUEST)

    # Check if email is a Google OAuth account
    user = db.session.query(User).filter_by(email=args["email"]).first()
    if user and user.is_google_account:
        return error_response(
            "This email is associated with a Google account. Please log in using Google",
            ErrorType.BAD_REQUEST,
        )

    # Check if email is taken
    if user:
        return error_response(
            "This email is taken. Please log in.", ErrorType.BAD_REQUEST
        )

    # Check existing phone
    # Format phone number
    formatted_phone = format_phone(args["phone"])
    if db.session.query(User).filter_by(phone=formatted_phone).first():
        return error_response("Phone is already taken", ErrorType.BAD_REQUEST)

    # If google, no need to check password
    if is_google_account:
        return None

    # Validate password
    valid, msg = validate_password(args["password"])
    if not valid:
        return error_response(msg, ErrorType.BAD_REQUEST)

    return None


# pylint: enable=too-many-return-statements


def get_user_school(
    school_name: Optional[str],
) -> Tuple[Optional[School], Optional[ResponseReturnValue]]:
    """Get school for user signup."""
    if school_name:
        school = db.session.query(School).filter_by(name=school_name).first()
    else:
        school = db.session.query(School).filter_by(name="Cornell University").first()

    if not school:
        return None, error_response("Invalid school.", ErrorType.BAD_REQUEST)
    return school, None


def get_user_major(
    major_name: str, school_id: int
) -> Tuple[Optional[Major], Optional[ResponseReturnValue]]:
    """Get major for user signup."""
    major = (
        db.session.query(Major).filter_by(name=major_name, school_id=school_id).first()
    )
    if not major:
        return None, error_response("Invalid Major.", ErrorType.BAD_REQUEST)
    return major, None


def get_user_language(
    language: Optional[str],
) -> Tuple[Optional[SupportedLanguagesEnum], Optional[ResponseReturnValue]]:
    """Get user language preference."""
    # No language preference
    if not language:
        return SupportedLanguagesEnum.ENGLISH, None

    # Valid language
    if language in SupportedLanguagesEnum.keys():
        return language, None

    # Invalid language
    return None, error_response(
        f"Invalid language: {language} is not one of {' '.join(SupportedLanguagesEnum.keys())}",
        ErrorType.BAD_REQUEST,
    )


def generate_unique_username() -> Optional[str]:
    """Generate unique username for new user."""
    n = 3
    counter = 0
    while counter < 100:
        username = generate_funny_username(n)
        if not db.session.query(User).filter_by(username=username).first():
            return username
        if counter > 10:
            n += 1
        counter += 1
    return None


def make_login_response(user: User, remember: bool) -> ResponseReturnValue:
    """Make a login response for the user."""
    # Generate and commit the access token for the user
    access_token = user.get_access_token()
    commit_changes("Failed to generate access token")

    # Make the response and set the access token
    response = jsonify(
        {"access_token": access_token, "user": user.to_dict(simplified=True)}
    )
    set_access_cookies(response, access_token)

    # Set the refresh token if the user wants to be remembered
    if remember:
        set_refresh_cookies(
            response,
            generate_refresh_token(user),
            max_age=current_app.config["JWT_REFRESH_TOKEN_EXPIRES"],
        )

    return response


def prepare_user_args(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare and clean user creation arguments.

    Args:
        args: Dictionary of user arguments

    Returns:
        Dictionary of cleaned and prepared arguments
    """
    # Clean string inputs
    cleaned_args = {}
    for key, value in args.items():
        if isinstance(value, str):
            cleaned_args[key] = value.strip()
        else:
            cleaned_args[key] = value

    return {
        "firstname": cleaned_args.get(
            "firstname", ""
        ),  # Will be replaced with username if empty
        "lastname": cleaned_args.get(
            "lastname", ""
        ),  # Will be replaced with username if empty
        "email": cleaned_args.get("email"),
        "phone": cleaned_args.get("phone"),
        "school": cleaned_args.get("school", ""),
        "major": cleaned_args.get("major", ""),
        "graduation": cleaned_args.get("graduation"),
        "language": cleaned_args.get("language", ""),
        "password": cleaned_args.get("password"),
    }


# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
def create_new_user(
    firstname: str,
    lastname: str,
    email: str,
    phone: str,
    school: str,
    major: str,
    graduation: str,
    language: str,
    password: Optional[str] = None,
    is_google_account: bool = False,
) -> Tuple[Optional[User], Optional[ResponseReturnValue]]:
    """
    Create a new user with the given parameters.

    Args:
        firstname: User's first name
        lastname: User's last name
        email: User's email
        phone: User's phone number
        school: Name of user's school
        major: Name of user's major
        graduation: User's graduation date
        language: User's preferred language
        password: User's password (None for Google accounts)
        is_google_account: Whether this is a Google OAuth account

    Returns:
        Tuple containing:
        - User object if creation successful, None otherwise
        - Error response if creation failed, None otherwise
    """
    # Get school
    school, error = get_user_school(school)
    if error:
        return None, error

    # Get major
    major, error = get_user_major(major, school.id)
    if error:
        return None, error

    # Get language
    language, error = get_user_language(language)
    if error:
        return None, error

    # Generate unique username
    username = generate_unique_username()
    if not username:
        return None, error_response("Ran out of usernames", ErrorType.INTERNAL_ERROR)

    # Create user
    user = User(
        username=username,
        firstname=firstname or username,  # Use username if firstname is empty
        lastname=lastname or username,  # Use username if lastname is empty
        email=email,
        phone=format_phone(phone),
        password=User.hash_password(password) if password else None,
        school_id=school.id,
        major_id=major.id,
        graduation=graduation,
        language=language,
        is_google_account=is_google_account,
        mail_is_verified=is_google_account,  # Google accounts are pre-verified
    )

    # Save user
    db.session.add(user)
    commit_error = commit_changes("Failed to create user")
    if commit_error:
        return None, commit_error

    # Create welcome notification
    create_notification(
        NotificationTypeEnum.ACCOUNT_CREATED,
        f"Welcome {username}!",
        user.id,
        None,
    )

    return user, None


# pylint: enable=all
