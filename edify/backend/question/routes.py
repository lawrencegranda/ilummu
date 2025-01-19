"""Question management endpoints for the Edify backend."""

# Standard Library imports
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from io import BytesIO
import mimetypes
from typing import Optional
import uuid

# Third-Party Framework imports
from flask import Blueprint, current_app, jsonify, request
from flask.typing import ResponseReturnValue
from flask_jwt_extended import jwt_required
from PIL import Image
from sqlalchemy.exc import IntegrityError
from webargs import fields
from webargs.flaskparser import use_args

# Local Application imports
from edify import db
from edify.backend.question.utils import question_dictionary
from edify.backend.user.utils import get_current_user, check_author
from edify.models import (
    Course,
    Method,
    Question,
    Notification,
    Offer,
)
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


def upload_image(file) -> Optional[str]:
    """
    Uploads a file to Filebase, resizing it if necessary, and returns its IPFS Gateway URL.

    Args:
        file: A file to be uploaded.

    Returns:
        Optional[str]: URL of uploaded image via the IPFS Gateway, or None if the upload fails.

    Raises:
        Exception: Any exception encountered during image processing or upload is caught and logged.
    """
    bucket_name = current_app.config["FILEBASE_BUCKET"]

    # Generate a unique key by combining a UUID, timestamp, and original filename
    timestamp = datetime.now(timezone.utc)
    key_name = f"images/{uuid.uuid4().hex}_{timestamp}_{file.filename}"

    # Upload image to Filebase
    try:

        # If it is an image, resize
        try:
            # Create a copy of the original file in memory
            file_copy = BytesIO(file.read())
            file_copy.seek(0)
            file.seek(0)

            # Open and process the image
            image = Image.open(file_copy)

            # Resize image (e.g., to 1024x1024 while keeping the aspect ratio)
            max_size = (1024, 1024)
            image.thumbnail(max_size)

            # Save the resized image to a BytesIO object
            image_bytes = BytesIO()
            image.save(image_bytes, format=image.format)
            image_bytes.seek(0)

            file = image_bytes
        except (IOError, OSError) as e:
            print("ERROR: Encountered an error resizing the image:", e)

        # Determine the MIME type of the file
        content_type, _ = mimetypes.guess_type(key_name)
        print(content_type)
        if not content_type:
            # Fallback if MIME type can't be determined
            content_type = "binary/octet-stream"

        # Upload the file with the specified ContentType
        aws_response = current_app.config["S3_CLIENT"].put_object(
            Body=file,
            Bucket=bucket_name,
            Key=key_name,
            ContentType=content_type,
        )

        # Try to get the CID from the response headers
        cid = aws_response["ResponseMetadata"]["HTTPHeaders"].get("x-amz-meta-cid")

        if cid:
            # Construct the IPFS Gateway URL using the CID
            image_url = f"{current_app.config['FILEBASE_URL']}{cid}"
            return image_url
    except (
        current_app.config["S3_CLIENT"].exceptions.ClientError,
        current_app.config["S3_CLIENT"].exceptions.BotoCoreError,
    ) as e:
        print("ERROR: Encountered an error uploading the image:", e)

    return None


def validate_question_creation(
    school_id: int, course_id: int, method: int
) -> Optional[tuple]:
    """
    Validate a question request.
    """
    # Fetch the method. Return error if invalid
    method = db.session.query(Method).filter_by(value=method).one_or_none()
    if method is None:
        return error_response("Invalid method", ErrorType.BAD_REQUEST)

    # Attempt to find the course by ID. Return error if invalid
    course = db.session.get(Course, course_id)
    if course is None:
        return error_response(
            "Invalid course",
            ErrorType.BAD_REQUEST,
        )
    if course.school_id != school_id:
        return error_response(
            "Course not in the user's school",
            ErrorType.BAD_REQUEST,
        )

    return None


# Endpoint: /backend/question/new
@question.route("/new", methods=["POST"])
@jwt_required()
@use_args(QuestionSchema, location="form")
def create_question(args):
    """
    Create a new question and post it in the database.

    Args:
        course_id (int): The course id for the question.
        method (int): The communication method ID.
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

    # No double requests
    recent_question = (
        db.session.query(Question)
        .filter_by(user_id=user.id)
        .order_by(Question.created_at.desc())
        .first()
    )
    if recent_question and datetime.now(
        timezone.utc
    ) - recent_question.created_at < timedelta(seconds=10):
        return error_response(
            "Too many requests, wait",
            ErrorType.BAD_REQUEST,
        )

    # Validate the question request
    checks = validate_question_creation(
        user.school_id, args["course_id"], args["method"]
    )
    if checks:
        return checks

    method = db.session.query(Method).filter_by(value=args["method"]).one_or_none()
    course = db.session.get(Course, args["course_id"])

    # Default to no image url
    image_url = None

    # Retrive the file
    image_file = request.files.get("image", default=None)
    if image_file:
        image_url = upload_image(image_file)
        if not image_url:
            return error_response("Failed to upload image.", ErrorType.INTERNAL_ERROR)

    # Create a new question associated with the user and course
    question_obj = Question(
        user_id=user.id,
        course_id=course.id,
        request=args["request_message"],
        solve_time=args["solve_time"],
        price=args["price"],
        method_id=method.id,
        solved=False,  # Question is initially unsolved
        image_url=image_url,
    )

    db.session.add(question_obj)

    # Commit and roll back if there's a database error
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f"IntegrityError: {e}")
        return error_response("Failed to create question.", ErrorType.BAD_REQUEST)

    # Create a notification for the new question
    create_notification(
        NotificationTypeEnum.QUESTION_CREATED,
        "Question created successfully.",
        question_obj.user.id,
        question_obj.id,
    )

    # Return the created question as a JSON response with status 201 (Created)
    return jsonify(question_obj.to_dict(simplified=True)), HTTPStatus.CREATED


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
    question_obj = db.session.query(Question).filter_by(id=id_question).first()

    # Return an error response if the question does not exist
    if not question_obj:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # If question is not visible, return an error response
    if not question_obj.visible:
        return error_response("Question is hidden", ErrorType.UNAUTHORIZED)

    # Set to not visible as deleted
    question_obj.visible = False
    db.session.commit()

    # Create a notification for the updated question
    create_notification(
        NotificationTypeEnum.QUESTION_DELETED,
        "Question deleted successfully.",
        question_obj.user.id,
        question_obj.id,
    )

    # Return the updated question as a JSON response with status 200 (OK)
    return jsonify(question_obj.to_dict(simplified=True)), HTTPStatus.OK


# Endpoint: /backend/question/all
@question.route("/all", methods=["GET"])
@jwt_required(optional=True)
def get_all() -> ResponseReturnValue:
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
def get(id_question: int) -> ResponseReturnValue:
    """
    Fetch a specific question by its ID.

    Args:
        id_question (int): The ID of the question to fetch.

    Returns:
        JSON response with the specified question or an error if not found.
    """
    # Query the Question model to find the question by its ID
    question_obj = db.session.query(Question).filter_by(id=id_question).first()

    # If no question is found, return an error response
    if not question_obj:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # If question is not visible, return an error response
    if not question_obj.visible:
        return error_response("Question is hidden", ErrorType.UNAUTHORIZED)

    # Get the current user from the JWT
    user = get_current_user()
    user_id = user.id if user else None

    # Convert the question object to a dictionary format suitable for JSON response
    qstn_dict = question_dictionary(user_id, question_obj.to_dict(simplified=False))

    # Return the question data in JSON format with HTTP 200 OK status
    return data_response(qstn_dict)


# Endpoint: /backend/question/<id_question>/is_author
@question.route("/<int:id_question>/is_author", methods=["GET"])
@jwt_required()
def is_author(id_question: int) -> ResponseReturnValue:
    """
    Check if the current user is the author of a specific question.

    Args:
        id_question (int): The ID of the question to check.

    Returns:
        JSON response with a boolean indicating if the user is the author or an error if not found.
    """
    # Query the Question model to find the question by its ID
    question_obj = db.session.query(Question).filter_by(id=id_question).first()

    # Return an error response if the question does not exist
    if not question_obj:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # If question is not visible, return an error response
    if not question_obj.visible:
        return error_response("Question is hidden", ErrorType.UNAUTHORIZED)

    # Get the current user from the JWT
    user = get_current_user()

    # Return an error response if the user is not found
    if not user:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    # Check if the current user is the author of the question
    user_is_author = check_author(user.id, question_obj.id)

    # Return the result as a JSON response
    return data_response(user_is_author)


# Endpoint: /backend/question/<id_question>/offer
@question.route("/<int:id_question>/offer", methods=["GET"])
@jwt_required()
def offer(id_question: int) -> ResponseReturnValue:
    """
    Check if the current user has made an offer for a specific question.

    Args:
        id_question (int): The ID of the question to check for an offer.

    Returns:
        JSON response with offer details if found or an empty list if not.
    """
    # Query the Question model to find the question by its ID
    question_obj = db.session.query(Question).filter_by(id=id_question).first()

    # Return an error response if the question does not exist
    if not question_obj:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # If question is not visible, return an error response
    if not question_obj.visible:
        return error_response("Question is hidden", ErrorType.UNAUTHORIZED)

    # Get the current user from the JWT
    user = get_current_user()

    # Return an error response if the user is not found
    if not user:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    # Query the Offer model to check if the user has made an active offer for the question
    offer_made = (
        db.session.query(Offer)
        .filter_by(question_id=question_obj.id, user_id=user.id, active=True)
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
def offers(id_question: int) -> ResponseReturnValue:
    """
    Fetch all offers received for a specific question.

    Args:
        id_question (int): The ID of the question to fetch offers for.

    Returns:
        JSON response with a list of offers or an error if the user is not the author.
    """
    # Query the Question model to find the question by its ID
    question_obj = db.session.query(Question).filter_by(id=id_question).first()

    # Return an error response if the question does not exist
    if not question_obj:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # If question is not visible, return an error response
    if not question_obj.visible:
        return error_response("Question is hidden", ErrorType.UNAUTHORIZED)

    # Query the Offer model for all active offers received for the specified question
    offer_list = (
        db.session.query(Offer)
        .filter_by(question_id=question_obj.id, active=True)
        .all()
    )

    # Convert the list of offers to a dictionary format suitable for JSON response
    offer_list = Offer.to_dict_all(offer_list)

    # Return the list of offers in JSON format with HTTP 200 OK status
    return data_response(offer_list)


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
def change_price(args, id_question: int) -> ResponseReturnValue:
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
    question_obj = db.session.query(Question).filter_by(id=id_question).first()

    # Return an error response if the question does not exist
    if not question_obj:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    # If question is not visible, return an error response
    if not question_obj.visible:
        return error_response("Question is hidden", ErrorType.UNAUTHORIZED)

    # If new price is too low, error
    if price < question_obj.original_price:
        return error_response("New price is too low", ErrorType.BAD_REQUEST)

    # If new price is too high, error
    if price > 3 * question_obj.original_price:
        return error_response("New price is too high", ErrorType.BAD_REQUEST)

    question_obj.price = price
    db.session.commit()

    # Create a notification for the updated question
    create_notification(
        NotificationTypeEnum.QUESTION_UPDATED,
        f"Question price updated to ${price:.2f}!",
        question_obj.user.id,
        question_obj.id,
    )

    # Send notifications to those who made an offer.
    offer_list = (
        db.session.query(Offer)
        .filter_by(question_id=question_obj.id, active=True)
        .all()
    )

    for offer_obj in offer_list:
        create_notification(
            NotificationTypeEnum.PRICE_CHANGE,
            (
                f"{question_obj.user.username} updated the question price to ${price:.2f}! "
                "Check your offer."
            ),
            user_id=offer_obj.user.id,
            question_id=question_obj.id,
        )

    # Return the updated question as a JSON response with status 200 (OK)
    return jsonify(question_obj.to_dict(simplified=True)), HTTPStatus.OK
