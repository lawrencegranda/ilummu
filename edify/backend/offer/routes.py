"""
Offer routes
"""

# Standard Library imports
from http import HTTPStatus
from typing import Optional

# Third-Party Framework imports
from flask import Blueprint, jsonify
from flask import typing as flask_typing
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
from webargs import fields
from webargs.flaskparser import use_args

# Local Application imports
from edify import db
from edify.models import Question, Offer, Notification
from edify.utils.constants import ErrorType, NotificationTypeEnum, OfferStatusEnum
from edify.backend.user.utils import get_current_user
from edify.utils.utils import error_response

# -----------------------------------------------------------------------------
# Route Blueprint
# -----------------------------------------------------------------------------
# Endpoint: /offer/
offer = Blueprint("offer", __name__, url_prefix="/offer")


# -----------------------------------------------------------------------------
# Blueprint Endpoints (offer)
# -----------------------------------------------------------------------------


def commit_offer_changes(error_msg: str) -> Optional[flask_typing.ResponseReturnValue]:
    """Commit changes and handle potential errors.

    Args:
        error_msg: Error message if commit fails

    Returns:
        Error response if commit fails, None if successful
    """
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f"IntegrityError: {e}")
        return error_response(error_msg, ErrorType.BAD_REQUEST)
    return None


def create_offer_notification(
    notification_type: str, message: str, user_id: int, question_id: int
) -> None:
    """Create and commit a notification for an offer."""
    notification = Notification(
        type=notification_type,
        message=message,
        user_id=user_id,
        question_id=question_id,
    )
    db.session.add(notification)
    db.session.commit()


def validate_offer_request(
    offer_id: int, require_author=False, require_owner=False
) -> Optional[tuple]:
    """Validate common offer request conditions."""
    user = get_current_user()
    if not user:
        return error_response("User does not exist", ErrorType.USER_NOT_FOUND)

    offer_obj = db.session.query(Offer).filter_by(id=offer_id).first()
    if not offer_obj:
        return error_response("Offer not found", ErrorType.NOT_FOUND)

    question = db.session.query(Question).filter_by(id=offer_obj.question_id).first()
    if not question:
        return error_response("Question does not exist", ErrorType.NOT_FOUND)

    auth_checks = [
        (
            require_author and question.user_id != user.id,
            "User is not author of the question",
        ),
        (
            require_owner and offer_obj.user_id != user.id,
            "User is not owner of the offer",
        ),
    ]

    for check, msg in auth_checks:
        if check:
            return error_response(msg, ErrorType.UNAUTHORIZED)

    status_checks = [
        (question.solved, "Question is already solved"),
        (not question.visible, "Question is not visible"),
        (not offer_obj.active, "Offer is not active"),
        (offer_obj.status == OfferStatusEnum.ACCEPTED, "Offer is already accepted"),
        (offer_obj.status == OfferStatusEnum.DECLINED, "Offer is already declined"),
        (offer_obj.status != OfferStatusEnum.SENT, "Offer status is not SENT"),
    ]

    for check, msg in status_checks:
        if check:
            return error_response(msg, ErrorType.BAD_REQUEST)

    return None


def validate_price(
    price: float, question_price: float
) -> Optional[flask_typing.ResponseReturnValue]:
    """Validate offer price is within acceptable range.

    Args:
        price: Proposed offer price
        question_price: Original question price

    Returns:
        Error response if invalid, None if valid
    """
    if not question_price <= price <= 2 * question_price:
        return error_response(
            "Price must be between original and 2x original", ErrorType.BAD_REQUEST
        )
    return None


# Endpoint: /backend/offer/new
@offer.route("/new", methods=["POST"])
@jwt_required()
@use_args(
    {
        "question_id": fields.Integer(required=True),
        "price": fields.Float(required=True),
    }
)
def create_offer(args) -> flask_typing.ResponseReturnValue:
    """Create an offer for a question."""
    user = get_current_user()
    if not user:
        return error_response("User does not exist", ErrorType.USER_NOT_FOUND)

    question = db.session.query(Question).filter_by(id=args["question_id"]).first()
    if not question:
        return error_response("Question does not exist", ErrorType.NOT_FOUND)

    existing_offer = (
        db.session.query(Offer)
        .filter_by(question_id=question.id, user_id=user.id, active=True)
        .first()
    )

    validation_checks = [
        (question.solved, "Question is already solved"),
        (not question.visible, "Question is not visible"),
        (existing_offer, "User already made offer to question"),
    ]

    for check, msg in validation_checks:
        if check:
            return error_response(msg, ErrorType.BAD_REQUEST)

    # Validate price
    price = args["price"]
    price_error = validate_price(price, question.price)
    if price_error:
        return price_error

    # Create and save offer
    offer_obj = Offer(
        user_id=user.id,
        question_id=question.id,
        amount=price,
    )
    db.session.add(offer_obj)

    commit_error = commit_offer_changes("Failed to create offer.")
    if commit_error:
        return commit_error

    # Send notifications
    notifications = [
        (
            NotificationTypeEnum.NEW_OFFER,
            f"You made a new offer for ${price:.2f}!",
            user.id,
        ),
        (
            NotificationTypeEnum.NEW_OFFER,
            f"You have a new offer from {user.username} for ${price:.2f}!",
            question.user_id,
        ),
    ]

    for n_type, msg, u_id in notifications:
        create_offer_notification(n_type, msg, u_id, question.id)

    return jsonify(offer_obj.to_dict(simplified=True)), HTTPStatus.CREATED


# Endpoint: /backend/offer/<int:id_offer>
@offer.route("/<int:id_offer>", methods=["GET"])
@jwt_required()
def get_offer(id_offer: int) -> flask_typing.ResponseReturnValue:
    """
    Retrieve an offer by its ID.

    Args:
        id_offer (int): The ID of the offer to retrieve.

    Returns:
        flask_typing.ResponseReturnValue: The response containing the offer data.
    """

    offer_obj = db.session.query(Offer).filter_by(id=id_offer).first()

    # If no offer is found, return an error response
    if not offer_obj:
        return error_response("Offer not found", ErrorType.NOT_FOUND)

    return jsonify(offer_obj.to_dict()), HTTPStatus.OK


# Endpoint: /backend/offer/<int:id_offer>
@offer.route("/<int:id_offer>", methods=["PUT"])
@jwt_required()
@use_args({"amount": fields.Float(required=True)})
def update_offer(args, id_offer: int) -> flask_typing.ResponseReturnValue:
    """Update an offer price."""
    # Validate offer request
    checks = validate_offer_request(id_offer, require_owner=True)
    if checks:
        return checks

    offer_obj = db.session.query(Offer).filter_by(id=id_offer).first()
    question = db.session.query(Question).filter_by(id=offer_obj.question_id).first()

    # Validate new amount
    new_amount = args["amount"]
    if not question.price <= new_amount <= 2 * question.price:
        return error_response("Invalid offer amount", ErrorType.BAD_REQUEST)

    offer_obj.amount = new_amount

    error = commit_offer_changes("Couldn't update offer")
    if error:
        return error

    # Send notifications
    create_offer_notification(
        NotificationTypeEnum.UPDATED_OFFER,
        f"You changed the offer amount to ${new_amount:.2f}!",
        offer_obj.user_id,
        question.id,
    )

    create_offer_notification(
        NotificationTypeEnum.UPDATED_OFFER,
        f"{offer_obj.user.username} changed their offer to ${new_amount:.2f}!",
        question.user_id,
        question.id,
    )

    return jsonify(offer_obj.to_dict()), HTTPStatus.OK


# Endpoint: /backend/offer/<int:id_offer>
@offer.route("/<int:id_offer>", methods=["DELETE"])
@jwt_required()
def delete_offer(id_offer: int) -> flask_typing.ResponseReturnValue:
    """Delete an offer from the database."""
    # Validate offer request
    checks = validate_offer_request(id_offer, require_owner=True)
    if checks:
        return checks

    offer_obj = db.session.query(Offer).filter_by(id=id_offer).first()
    question = db.session.query(Question).filter_by(id=offer_obj.question_id).first()

    offer_obj.status = OfferStatusEnum.REMOVED
    offer_obj.active = False

    error = commit_offer_changes("Couldn't delete offer")
    if error:
        return error

    # Send notifications
    create_offer_notification(
        NotificationTypeEnum.OFFER_REVOKED,
        f"You revoked an offer to {question.user.username}!",
        offer_obj.user_id,
        question.id,
    )

    create_offer_notification(
        NotificationTypeEnum.OFFER_REVOKED,
        f"{offer_obj.user.username} revoked their offer!",
        question.user_id,
        question.id,
    )

    return jsonify({"msg": "Offer deleted"}), HTTPStatus.NO_CONTENT


# Endpoint: /backend/offer/user/<int:user_id>
@offer.route("/user/<int:user_id>", methods=["GET"])
@jwt_required()
def get_offers_by_user(user_id: int) -> flask_typing.ResponseReturnValue:
    """
    Retrieves offers associated with a specific user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        flask_typing.ResponseReturnValue: Response containing the offers associated with the user.
    """
    user = get_current_user()

    # Check if user exists
    if not user:
        return error_response("User does not exist", ErrorType.USER_NOT_FOUND)

    offers = Offer.query.filter_by(user_id=user_id, active=True).all()
    return jsonify(Offer.to_dict_all(offers)), HTTPStatus.OK


@offer.route("/accept/<int:offer_id>", methods=["POST"])
@jwt_required()
def accept_offer(offer_id: int) -> flask_typing.ResponseReturnValue:
    """Accept an offer for a question."""
    # Validate offer request
    checks = validate_offer_request(offer_id, require_author=True)
    if checks:
        return checks

    offer_obj = db.session.query(Offer).filter_by(id=offer_id).first()
    question = db.session.query(Question).filter_by(id=offer_obj.question_id).first()

    # Update offer and related offers
    offer_obj.status = OfferStatusEnum.ACCEPTED
    question.solved = True

    # Decline other active offers
    other_offers = (
        db.session.query(Offer)
        .filter(
            Offer.question_id == question.id,
            Offer.id != offer_id,
            Offer.active.is_(True),
        )
        .all()
    )

    for other_offer in other_offers:
        other_offer.status = OfferStatusEnum.DECLINED
        other_offer.active = False

    error = commit_offer_changes("Couldn't accept offer")
    if error:
        return error

    # Send notifications
    create_offer_notification(
        NotificationTypeEnum.OFFER_ACCEPTED,
        (
            f"Your offer to {question.user.username} was accepted! Check the "
            "question information as soon as possible to get in touch with them."
        ),
        offer_obj.user_id,
        question.id,
    )

    create_offer_notification(
        NotificationTypeEnum.OFFER_ACCEPTED,
        (
            f"You accepted {offer_obj.user.username}'s offer! Check the question "
            "information as soon as possible to get in touch with them."
        ),
        question.user_id,
        question.id,
    )

    for other_offer in other_offers:
        create_offer_notification(
            NotificationTypeEnum.OFFER_DECLINED,
            f"Your offer to {question.user.username} was declined!",
            other_offer.user_id,
            question.id,
        )

    return jsonify(offer_obj.to_dict()), HTTPStatus.OK


# Endpoint: /backend/offer/decline/<int:offer_id>
@offer.route("/decline/<int:offer_id>", methods=["POST"])
@jwt_required()
def decline_offer(offer_id: int) -> flask_typing.ResponseReturnValue:
    """Decline an offer for a question."""
    # Validate offer request
    checks = validate_offer_request(offer_id, require_author=True)
    if checks:
        return checks

    offer_obj = db.session.query(Offer).filter_by(id=offer_id).first()
    question = db.session.query(Question).filter_by(id=offer_obj.question_id).first()

    # Update offer status
    offer_obj.status = OfferStatusEnum.DECLINED
    offer_obj.active = False

    error = commit_offer_changes("Couldn't decline offer")
    if error:
        return error

    # Send notifications
    create_offer_notification(
        NotificationTypeEnum.OFFER_DECLINED,
        f"Your offer to {question.user.username} was declined!",
        offer_obj.user_id,
        question.id,
    )

    create_offer_notification(
        NotificationTypeEnum.OFFER_DECLINED,
        f"You declined {offer_obj.user.username}'s offer!",
        question.user_id,
        question.id,
    )

    return jsonify(offer_obj.to_dict()), HTTPStatus.OK
