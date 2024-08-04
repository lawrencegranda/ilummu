# Standard Library imports
from typing import Optional
from datetime import datetime

# Third-Party Framework imports
from flask_jwt_extended import current_user
from flask_login import UserMixin

# Local Application imports
from edify.models import User, Question


def get_current_user() -> Optional[User]:
    """
    Helper function to get the current user.

    Returns:
        Optional[User]: The current user if authenticated, otherwise None.
    """
    return current_user if isinstance(current_user, UserMixin) else None


def generate_access_token(user: User) -> str:
    """
    Generate an access token for the user and update the user's token information.

    Args:
        user (User): The user for whom the access token is generated.

    Returns:
        str: The generated access token.
    """
    access_token = user.get_reset_token()
    user.token = access_token
    user.token_last_refresh = datetime.utcnow()
    return access_token


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
