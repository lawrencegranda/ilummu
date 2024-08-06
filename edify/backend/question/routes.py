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
from edify.models import AcademicField, Course, Method, Question, User
from edify.utils.constants import ErrorType
from edify.utils.utils import error_response

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
@use_args(
    {
        "class_code": fields.Str(required=True, validate=validate.Length(min=4)),
        "class_name": fields.Str(required=True, validate=validate.Length(min=1)),
        "academic_field": fields.Str(required=True, validate=validate.Length(min=1)),
        "method_id": fields.Int(required=True),
        "solve_time": fields.Int(required=True, validate=validate.Range(min=1)),
        "price": fields.Float(required=True, validate=validate.Range(min=0)),
        "request_message": fields.Str(required=True, validate=validate.Length(min=1)),
    }
)
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
    method = db.session.get(Method, args.get("method_id"))
    if method is None:
        return error_response("Invalid method ID", ErrorType.BAD_REQUEST)

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
        method_id=args["method_id"],
        solved=False,  # Question is initially unsolved
    )

    db.session.add(question)

    # Commit and roll back if there's a database error
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response("Failed to create question.", ErrorType.BAD_REQUEST)

    # Return the created question as a JSON response with status 201 (Created)
    return jsonify(question.to_dict(simplified=True)), HTTPStatus.CREATED


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

    # Get all questions and
    questions = Question.to_dict_all(
        db.session.query(Question).filter_by(visible=True).all()
    )
    questions = [question_dictionary(user_id, q) for q in questions]

    return jsonify({"data": questions}), HTTPStatus.OK
