from flask import Blueprint, url_for, jsonify, current_app, redirect
from flask_jwt_extended import jwt_required, current_user
from edify.backend.user.routes import get_current_user
from edify.models import (
    User,
    Notification,
    AcademicField,
    Method,
    TimeInterval,
    Course,
    School,
    NotificationType,
    Major,
    Question,
    Notification,
    Offer,
)
from edify import db
from http import HTTPStatus
from edify.utils.utils import internal_request, error_response
from edify.utils.constants import ErrorType
from edify.utils.decorators import author_required

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
def fetch_user_subjects():
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
def fetch_school_subjects(id_school):
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
def fetch_user_majors():
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
def fetch_school_majors(id_school):
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
def fetch_methods():
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
def fetch_intervals():
    """
    Fetch all time intervals.

    Returns:
        JSON response with the time intervals.
    """
    time_intervals = TimeInterval.to_dict_all(db.session.query(TimeInterval).all())
    return jsonify({"data": time_intervals}), HTTPStatus.OK


# Endpoint: /data/notifications
@data.route("/notifications", methods=["GET"])
def fetch_user_notifications():
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
def fetch_questions():
    """
    Fetch all questions available in the system.

    Returns:
        JSON response with all questions.
    """
    questions = Question.to_dict_all(db.session.query(Question).all())
    return jsonify({"data": questions}), HTTPStatus.OK


# Endpoint: /data/question/<id_question>
@data.route("/question/<int:id_question>", methods=["GET"])
@jwt_required(optional=True)
def get_question(id_question):
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

    # Convert the question object to a dictionary format suitable for JSON response
    qstn_dict = Question.to_dict_all([question])[0]

    # Return the question data in JSON format with HTTP 200 OK status
    return jsonify({"data": [qstn_dict]}), HTTPStatus.OK


# Endpoint: /data/question/<id_question>/is_author
@data.route("/question/<int:id_question>/is_author", methods=["GET"])
@jwt_required()
def is_question_author(id_question):
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
    is_author = question.user_id == user.id

    # Return the result as a JSON response
    return jsonify({"data": [is_author]}), HTTPStatus.OK


# Endpoint: /data/question/<id_question>/offer_made
@data.route("/question/<int:id_question>/offer_made", methods=["GET"])
@jwt_required()
def question_offer_made(id_question):
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
def offers_received(id_question):
    """
    Fetch all offers received for a specific question.

    Args:
        id_question (int): The ID of the question to fetch offers for.

    Returns:
        JSON response with a list of offers or an error if the user is not the author.
    """
    # Query the Question model to find the question by its ID
    question = db.session.query(Question).get(id_question)

    # Get the current user from the JWT
    user = get_current_user()

    # Query the Offer model for all active offers received for the specified question
    offers = (
        db.session.query(Offer).filter_by(question_id=question.id, active=True).all()
    )

    # Convert the list of offers to a dictionary format suitable for JSON response
    offers = Offer.to_dict_all(offers)

    # Return the list of offers in JSON format with HTTP 200 OK status
    return jsonify({"data": offers}), HTTPStatus.OK
