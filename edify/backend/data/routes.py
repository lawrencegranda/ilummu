# Standard Library imports
from http import HTTPStatus
from typing import Any, Dict, List, Optional

# Third-Party Framework imports
from flask import Blueprint, current_app, jsonify, redirect, url_for
from flask import typing as flask_typing
from flask_jwt_extended import jwt_required, current_user

# Local Application imports
from edify import db
from edify.backend.user.utils import get_current_user, check_author
from edify.models import (
    AcademicField,
    Course,
    Major,
    Method,
    Notification,
    NotificationType,
    Offer,
    Question,
    School,
    TimeInterval,
    User,
)
from edify.utils.constants import ErrorType, OfferStatusEnum
from edify.utils.decorators import author_required
from edify.utils.utils import error_response, internal_request


# -----------------------------------------------------------------------------
# Route Blueprint
# -----------------------------------------------------------------------------
# Endpoint: /data/
data = Blueprint("data", __name__, url_prefix="/data")


# -----------------------------------------------------------------------------
# Blueprint Endpoints (data)
# -----------------------------------------------------------------------------


# Endpoint: /data/subjects
@data.route("/subjects", methods=["GET"])
@jwt_required(optional=True)
def fetch_user_subjects() -> flask_typing.ResponseReturnValue:
    """
    Fetch the subjects associated with the current user if authenticated,
    otherwise fetch subjects for 'Cornell University'.

    Returns:
        JSON response with the subjects.
    """
    user = get_current_user()
    if user:
        # If user is logged in, get their school
        school = user.school
    else:
        # If no user is logged in, default to Cornell University
        school = db.session.query(School).filter_by(name="Cornell University").first()

    # Call another endpoint to fetch subjects for the school
    response = internal_request(
        url_for("backend.data.fetch_school_subjects", id_school=school.id), method="GET"
    )
    return response


# Endpoint: /data/school/<id_school>/subjects
@data.route("/school/<int:id_school>/subjects", methods=["GET"])
def fetch_school_subjects(id_school: int) -> flask_typing.ResponseReturnValue:
    """
    Fetch all subjects for a given school ID.

    Args:
        id_school (int): The ID of the school to fetch subjects for.

    Returns:
        JSON response with the subjects related to the specified school.
    """
    subjects = AcademicField.to_dict_all(
        db.session.query(AcademicField).filter_by(school_id=id_school).all()
    )
    return jsonify({"data": subjects}), HTTPStatus.OK


# Endpoint: /data/majors
@data.route("/majors", methods=["GET"])
@jwt_required(optional=True)
def fetch_user_majors() -> flask_typing.ResponseReturnValue:
    """
    Fetch the majors associated with the current user if authenticated,
    otherwise fetch majors for 'Cornell University'.

    Returns:
        JSON response with the majors.
    """
    user = get_current_user()
    if user:
        # Fetch user's school if authenticated
        school = user.school
    else:
        # Default to Cornell University if not authenticated
        school = db.session.query(School).filter_by(name="Cornell University").first()

    # Call another endpoint to fetch majors for the school
    response = internal_request(
        url_for("backend.data.fetch_school_majors", id_school=school.id), method="GET"
    )
    return response


# Endpoint: /data/school/<id_school>/majors
@data.route("/school/<int:id_school>/majors", methods=["GET"])
def fetch_school_majors(id_school: int) -> flask_typing.ResponseReturnValue:
    """
    Fetch all majors for a given school ID.

    Args:
        id_school (int): The ID of the school to fetch majors for.

    Returns:
        JSON response with the majors related to the specified school.
    """
    majors = Major.to_dict_all(
        db.session.query(Major).filter_by(school_id=id_school).all()
    )
    return jsonify({"data": majors}), HTTPStatus.OK


# Endpoint: /data/methods
@data.route("/methods", methods=["GET"])
def fetch_methods() -> flask_typing.ResponseReturnValue:
    """
    Fetch all supported methods.

    Returns:
        JSON response with the supported methods.
    """
    methods = Method.to_dict_all(
        db.session.query(Method).filter_by(supported=True).all()
    )
    return jsonify({"data": methods}), HTTPStatus.OK


# Endpoint: /data/intervals
@data.route("/intervals", methods=["GET"])
def fetch_intervals() -> flask_typing.ResponseReturnValue:
    """
    Fetch all time intervals.

    Returns:
        JSON response with the time intervals.
    """
    time_intervals = TimeInterval.to_dict_all(db.session.query(TimeInterval).all())
    return jsonify({"data": time_intervals}), HTTPStatus.OK


# Endpoint: /data/notifications
@data.route("/notifications", methods=["GET"])
def fetch_user_notifications() -> flask_typing.ResponseReturnValue:
    """
    Fetch notifications for the current user.

    Returns:
        JSON response with the user's notifications or an error if user is not found.
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    # Collect notifications for the logged-in user
    notifications = []
    if user:
        notifications = Notification.to_dict_all(user.notifications)

    return jsonify({"data": notifications}), HTTPStatus.OK


# Endpoint: /data/questions
@data.route("/questions", methods=["GET"])
@jwt_required(optional=True)
def fetch_questions() -> flask_typing.ResponseReturnValue:
    """
    Fetch all questions available in the system.

    Returns:
        JSON response with all questions.
    """
    # Get the current user from the JWT
    user = get_current_user()
    user_id = user.id if user else None

    questions = Question.to_dict_all(db.session.query(Question).all())
    questions = [question_dictionary(user_id, q) for q in questions]

    return jsonify({"data": questions}), HTTPStatus.OK


# Endpoint: /data/question/<id_question>
@data.route("/question/<int:id_question>", methods=["GET"])
@jwt_required(optional=True)
def get_question(id_question: int) -> flask_typing.ResponseReturnValue:
    """
    Fetch a specific question by its ID.

    Args:
        id_question (int): The ID of the question to fetch.

    Returns:
        JSON response with the specified question or an error if not found.
    """
    # Query the Question model to find the question by its ID
    question = db.session.query(Question).get(id_question)

    # If no question is found, return an error response
    if not question:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # Get the current user from the JWT
    user = get_current_user()
    user_id = user.id if user else None

    # Convert the question object to a dictionary format suitable for JSON response
    qstn_dict = question_dictionary(user_id, question.to_dict(simplified=False))

    # Return the question data in JSON format with HTTP 200 OK status
    return jsonify({"data": [qstn_dict]}), HTTPStatus.OK


# Endpoint: /data/question/<id_question>/is_author
@data.route("/question/<int:id_question>/is_author", methods=["GET"])
@jwt_required()
def is_question_author(id_question: int) -> flask_typing.ResponseReturnValue:
    """
    Check if the current user is the author of a specific question.

    Args:
        id_question (int): The ID of the question to check.

    Returns:
        JSON response with a boolean indicating if the user is the author or an error if not found.
    """
    # Query the Question model to find the question by its ID
    question = db.session.query(Question).get(id_question)

    # Return an error response if the question does not exist
    if not question:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # Get the current user from the JWT
    user = get_current_user()

    # Return an error response if the user is not found
    if not user:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    # Check if the current user is the author of the question
    is_author = check_author(user.id, question.id)

    # Return the result as a JSON response
    return jsonify({"data": [is_author]}), HTTPStatus.OK


# Endpoint: /data/question/<id_question>/offer_made
@data.route("/question/<int:id_question>/offer_made", methods=["GET"])
@jwt_required()
def question_offer_made(id_question: int) -> flask_typing.ResponseReturnValue:
    """
    Check if the current user has made an offer for a specific question.

    Args:
        id_question (int): The ID of the question to check for an offer.

    Returns:
        JSON response with offer details if found or an empty list if not.
    """
    # Query the Question model to find the question by its ID
    question = db.session.query(Question).get(id_question)

    # Return an error response if the question does not exist
    if not question:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # Get the current user from the JWT
    user = get_current_user()

    # Return an error response if the user is not found
    if not user:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    # Query the Offer model to check if the user has made an active offer for the question
    offer_made = (
        db.session.query(Offer)
        .filter_by(question_id=question.id, user_id=user.id, active=True)
        .first()
    )

    # If no offer is found, return an empty list
    if not offer_made:
        return jsonify({"data": []}), HTTPStatus.OK

    # Return the found offer details in JSON format
    return jsonify({"data": [offer_made.to_dict(simplified=False)]}), HTTPStatus.OK


# Endpoint: /data/question/<id_question>/offers_received
@data.route("/question/<int:id_question>/offers_received", methods=["GET"])
@jwt_required()
@author_required("id_question")
def offers_received(id_question: int) -> flask_typing.ResponseReturnValue:
    """
    Fetch all offers received for a specific question.

    Args:
        id_question (int): The ID of the question to fetch offers for.

    Returns:
        JSON response with a list of offers or an error if the user is not the author.
    """
    # Query the Question model to find the question by its ID
    question = db.session.query(Question).get(id_question)

    # Query the Offer model for all active offers received for the specified question
    offers = (
        db.session.query(Offer).filter_by(question_id=question.id, active=True).all()
    )

    # Convert the list of offers to a dictionary format suitable for JSON response
    offers = Offer.to_dict_all(offers)

    # Return the list of offers in JSON format with HTTP 200 OK status
    return jsonify({"data": offers}), HTTPStatus.OK


def question_dictionary(
    user_id: Optional[int], question_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Completes the given question dictionary with author status, offers,
    and offer statuses based on the user's ID.

    Args:
        user_id (Optional[int]): The ID of the user.
        question_dict (Dict[str, Any]): The dictionary containing question data.

    Returns:
        Dict[str, Any]: The updated question dictionary with additional information.
    """
    is_author = check_author(user_id, question_dict["id"])

    # Initialize offer-related variables
    offers = []
    offer_made = None
    offer_accepted = None

    if user_id:
        if is_author:
            # Fetch all active offers for the author's question
            offers = Offer.query.filter_by(
                question_id=question_dict["id"], active=True
            ).all()
            offers = Offer.to_dict_all(offers)

            # Attempt to get the accepted offer, if it exists
            offer_accepted = Offer.query.filter_by(
                question_id=question_dict["id"],
                active=True,
                status=OfferStatusEnum.ACCEPTED,
            ).one_or_none()
            offer_accepted = (
                offer_accepted.to_dict(simplified=False) if offer_accepted else None
            )
        else:
            # Fetch the made offer if the user is not the author
            offer_made = Offer.query.filter_by(
                question_id=question_dict["id"], user_id=user_id, active=True
            ).first()
            offer_made = offer_made.to_dict(simplified=False) if offer_made else None

    # Update the question dictionary with computed values
    question_dict["is_author"] = is_author
    question_dict["offers"] = offers
    question_dict["offer_made"] = offer_made
    question_dict["offer_accepted"] = offer_accepted

    return question_dict
