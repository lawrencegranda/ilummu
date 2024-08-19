# Standard Library imports
from http import HTTPStatus
from typing import Optional, Any, Tuple

# Third-Party Framework imports
from flask import Blueprint, Flask, jsonify
from flask import typing as flask_typing
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
from webargs import fields, validate
from webargs.flaskparser import use_args

# Local Application imports
from edify import db
from edify.backend.question.utils import question_dictionary
from edify.backend.user.utils import get_current_user
from edify.models import AcademicField, Course, Method, Question, User, Notification
from edify.utils.constants import ErrorType, QuestionSchema, NotificationTypeEnum
from edify.utils.decorators import author_required
from edify.utils.utils import error_response, data_response

# -----------------------------------------------------------------------------
# Route Blueprint
# -----------------------------------------------------------------------------
# Endpoint: /question/
question = Blueprint("question", __name__, url_prefix="/question")


# -----------------------------------------------------------------------------
# Blueprint Endpoints (question)
# -----------------------------------------------------------------------------


# Endpoint: /backend/question/new
@question.route("/new", methods=["POST"])
@jwt_required()
@use_args(QuestionSchema)
def create_question(args):
    """
    Create a new question and post it in the database.

    Args:
        class_code (str): The class code for the question.
        class_name (str): The name of the class.
        academic_field_id (int): The ID associated with the academic field.
        method_id (int): The communication method ID.
        solve_time (int): The required time to solve the question.
        price (float): The offered price for solving the question.
        request_message (str): The question/request message.

    Returns:
        dict: A JSON response containing a success message or an error message.
    """
    # Retrieve the current user. Return an error if no user is found
    user = get_current_user()
    if user is None:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    # Fetch the method. Return error if invalid
    method = db.session.query(Method).filter_by(value=args.get("method")).one_or_none()
    if method is None:
        return error_response("Invalid method", ErrorType.BAD_REQUEST)

    # Fetch the academic field. Return error if invalid
    academic_field = AcademicField.query.filter_by(
        value=args.get("academic_field"), school_id=user.school_id
    ).one_or_none()
    if academic_field is None:
        return error_response(
            f"Invalid academic field or not in {user.school.name}",
            ErrorType.BAD_REQUEST,
        )

    # Format code to uppercase
    args["class_code"] = args["class_code"].upper()

    # Format name to titlecase
    args["class_name"] = args["class_name"].title()

    # Attempt to find the course matching the provided class code and academic field
    course = Course.query.filter_by(
        code=args["class_code"],
        academic_field_id=academic_field.id,
        school_id=user.school_id,
    ).first()

    # If course does not exist, create a new course
    if not course:
        course = Course(
            code=args["class_code"],
            name=args["class_name"],
            academic_field_id=academic_field.id,
            school_id=user.school_id,
        )

        db.session.add(course)

        # Commit and roll back if there's a database error
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return error_response("Failed to create course.", ErrorType.BAD_REQUEST)

    # Create a new question associated with the user and course
    question = Question(
        user_id=user.id,
        course_id=course.id,
        request=args["request_message"],
        solve_time=args["solve_time"],
        price=args["price"],
        method_id=method.id,
        solved=False,  # Question is initially unsolved
    )

    db.session.add(question)

    # Commit and roll back if there's a database error
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response("Failed to create question.", ErrorType.BAD_REQUEST)

    # Create a notification for the new question
    notification = Notification(
        type=NotificationTypeEnum.QUESTION_CREATED,
        message=f"Question created successfully.",
        user_id=user.id,
        question_id=question.id,
    )
    db.session.add(notification)
    db.session.commit()

    # Return the created question as a JSON response with status 201 (Created)
    return jsonify(question.to_dict(simplified=True)), HTTPStatus.CREATED


# Endpoint: /backend/question/<int:id_question>/delete
@question.route("/<int:id_question>/delete", methods=["DELETE"])
@jwt_required()
@author_required("id_question")
def delete_question(id_question: int):
    """
    Delete a question by marking it not visible.

    Args:
        id_question (int): The question to delete

    Returns:
        dict: A JSON response containing the updated question or an error message.
    """
    # Retrieve the current user. Return an error if no user is found
    user = get_current_user()
    if user is None:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    # Query the Question model to find the question by its ID
    question = db.session.query(Question).filter_by(id=id_question).first()

    # Return an error response if the question does not exist
    if not question:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # If question is not visible, return an error response
    if not question.visible:
        return error_response("Question is hidden", ErrorType.UNAUTHORIZED)

    # Set to not visible as deleted
    question.visible = False
    db.session.commit()

    # Create a notification for the updated question
    notification = Notification(
        type=NotificationTypeEnum.QUESTION_DELETED,
        message=f"Question deleted successfully.",
        user_id=user.id,
        question_id=question.id,
    )
    db.session.add(notification)
    db.session.commit()

    # Return the updated question as a JSON response with status 200 (OK)
    return jsonify(question.to_dict(simplified=True)), HTTPStatus.OK


# Endpoint: /backend/question/all
@question.route("/all", methods=["GET"])
@jwt_required(optional=True)
def all() -> flask_typing.ResponseReturnValue:
    """
    Fetch all questions available in the system.

    Returns:
        JSON response with all questions.
    """
    # Get the current user from the JWT
    user = get_current_user()
    user_id = user.id if user else None

    # Get all questions
    questions = Question.to_dict_all(
        db.session.query(Question).filter_by(visible=True).all()
    )
    questions = [question_dictionary(user_id, q) for q in questions]

    return data_response(questions)


# Endpoint: /backend/question/<id_question>
@question.route("/<int:id_question>", methods=["GET"])
@jwt_required(optional=True)
def get(id_question: int) -> flask_typing.ResponseReturnValue:
    """
    Fetch a specific question by its ID.

    Args:
        id_question (int): The ID of the question to fetch.

    Returns:
        JSON response with the specified question or an error if not found.
    """
    # Query the Question model to find the question by its ID
    question = db.session.query(Question).filter_by(id=id_question).first()

    # If no question is found, return an error response
    if not question:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # If question is not visible, return an error response
    if not question.visible:
        return error_response("Question is hidden", ErrorType.UNAUTHORIZED)

    # Get the current user from the JWT
    user = get_current_user()
    user_id = user.id if user else None

    # Convert the question object to a dictionary format suitable for JSON response
    qstn_dict = question_dictionary(user_id, question.to_dict(simplified=False))

    # Return the question data in JSON format with HTTP 200 OK status
    return data_response(qstn_dict)


# Endpoint: /backend/question/<id_question>/is_author
@question.route("/<int:id_question>/is_author", methods=["GET"])
@jwt_required()
def is_author(id_question: int) -> flask_typing.ResponseReturnValue:
    """
    Check if the current user is the author of a specific question.

    Args:
        id_question (int): The ID of the question to check.

    Returns:
        JSON response with a boolean indicating if the user is the author or an error if not found.
    """
    # Query the Question model to find the question by its ID
    question = db.session.query(Question).filter_by(id=id_question).first()

    # Return an error response if the question does not exist
    if not question:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # If question is not visible, return an error response
    if not question.visible:
        return error_response("Question is hidden", ErrorType.UNAUTHORIZED)

    # Get the current user from the JWT
    user = get_current_user()

    # Return an error response if the user is not found
    if not user:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    # Check if the current user is the author of the question
    is_author = check_author(user.id, question.id)

    # Return the result as a JSON response
    return data_response(is_author)


# Endpoint: /backend/question/<id_question>/offer
@question.route("/<int:id_question>/offer", methods=["GET"])
@jwt_required()
def offer(id_question: int) -> flask_typing.ResponseReturnValue:
    """
    Check if the current user has made an offer for a specific question.

    Args:
        id_question (int): The ID of the question to check for an offer.

    Returns:
        JSON response with offer details if found or an empty list if not.
    """
    # Query the Question model to find the question by its ID
    question = db.session.query(Question).filter_by(id=id_question).first()

    # Return an error response if the question does not exist
    if not question:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # If question is not visible, return an error response
    if not question.visible:
        return error_response("Question is hidden", ErrorType.UNAUTHORIZED)

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
        return data_response()

    # Return the found offer details in JSON format
    return data_response(offer_made.to_dict(simplified=False))


# Endpoint: /backend/question/<id_question>/offers
@question.route("/<int:id_question>/offers", methods=["GET"])
@jwt_required()
@author_required("id_question")
def offers(id_question: int) -> flask_typing.ResponseReturnValue:
    """
    Fetch all offers received for a specific question.

    Args:
        id_question (int): The ID of the question to fetch offers for.

    Returns:
        JSON response with a list of offers or an error if the user is not the author.
    """
    # Query the Question model to find the question by its ID
    question = db.session.query(Question).filter_by(id=id_question).first()

    # Return an error response if the question does not exist
    if not question:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # If question is not visible, return an error response
    if not question.visible:
        return error_response("Question is hidden", ErrorType.UNAUTHORIZED)

    # Query the Offer model for all active offers received for the specified question
    offers = (
        db.session.query(Offer).filter_by(question_id=question.id, active=True).all()
    )

    # Convert the list of offers to a dictionary format suitable for JSON response
    offers = Offer.to_dict_all(offers)

    # Return the list of offers in JSON format with HTTP 200 OK status
    return data_response(offers)


# Endpoint: /backend/question/<id_question>
@question.route("/<int:id_question>", methods=["PUT"])
@jwt_required()
@use_args(
    {
        "price": fields.Float(required=True),
    },
    location="json",  # Change to "json" to read from the body
)
@author_required("id_question")
def change_price(args, id_question: int) -> flask_typing.ResponseReturnValue:
    """
    Change the price of the question.

    Args:
        id_question (int): The ID of the question to change.
        args (dict): Arguments containing the new price.

    Returns:
        JSON response.
    """
    # Retrieve the current user. Return an error if no user is found
    user = get_current_user()
    if user is None:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    price = args["price"]

    # Query the Question model to find the question by its ID
    question = db.session.query(Question).filter_by(id=id_question).first()

    # Return an error response if the question does not exist
    if not question:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # If question is not visible, return an error response
    if not question.visible:
        return error_response("Question is hidden", ErrorType.UNAUTHORIZED)

    # If new price is too low, error
    if price < question.original_price:
        return error_response("New price is too low", ErrorType.BAD_REQUEST)

    # If new price is too high, error
    if price > 2 * question.original_price:
        return error_response("New price is too high", ErrorType.BAD_REQUEST)

    question.price = price
    db.session.commit()

    # Create a notification for the updated question
    notification = Notification(
        type=NotificationTypeEnum.QUESTION_UPDATED,
        message=f"Question price updated to ${price:.2f}!",
        user_id=user.id,
        question_id=question.id,
    )
    db.session.add(notification)
    db.session.commit()

    # Return the updated question as a JSON response with status 200 (OK)
    return jsonify(question.to_dict(simplified=True)), HTTPStatus.OK
