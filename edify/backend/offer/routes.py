# Standard Library imports
from http import HTTPStatus
from typing import Optional, Any, Tuple
from datetime import datetime, timedelta

# Third-Party Framework imports
from flask import Blueprint, Flask, jsonify, redirect, url_for
from flask import typing as flask_typing
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
from webargs import fields, validate
from webargs.flaskparser import use_args
from sqlalchemy.exc import IntegrityError


# Local Application imports
from edify import db
from edify.models import User, Question, Offer, OfferStatus, Notification
from edify.utils.constants import ErrorType, OfferStatusEnum
from edify.backend.user.utils import get_current_user
from edify.utils.utils import error_response
from edify.utils.constants import ErrorType, NotificationTypeEnum, OfferStatusEnum
from socketio_ext import socketio

# -----------------------------------------------------------------------------
# Route Blueprint
# -----------------------------------------------------------------------------
# Endpoint: /offer/
offer = Blueprint("offer", __name__, url_prefix="/offer")


# -----------------------------------------------------------------------------
# Blueprint Endpoints (offer)
# -----------------------------------------------------------------------------


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
    """
    Create an offer for a question.

    Args:
        args (dict): A dictionary containing the arguments for creating the offer.

    Returns:
        flask_typing.ResponseReturnValue: A tuple containing the new offer and HTTP status code.
    """
    user = get_current_user()
    # Check if user exists
    if not user:
        return error_response("User does not exist", ErrorType.USER_NOT_FOUND)

    question_id = args["question_id"]
    # Check if question exists
    question = db.session.query(Question).filter_by(id=question_id).first()
    if not question:
        return error_response("Question does not exist", ErrorType.NOT_FOUND)

    # Check if user has made an unresolved offer to question
    existing_offer = (
        db.session.query(Offer)
        .filter_by(question_id=question_id, user_id=user.id, active=True)
        .first()
    )
    if existing_offer:
        return error_response(
            "User already made offer to question", ErrorType.BAD_REQUEST
        )

    # Check if question is visible and unsolved
    if question.solved:
        return error_response("Question is already solved", ErrorType.BAD_REQUEST)
    if not question.visible:
        return error_response("Question is not visible", ErrorType.BAD_REQUEST)

    # Check if price is reasonable
    price = args["price"]
    if price < question.price:
        return error_response("Price is too low", ErrorType.BAD_REQUEST)
    if price > 2 * question.price:
        return error_response("Price is too high", ErrorType.BAD_REQUEST)

    offer = Offer(
        user_id=user.id,
        question_id=question.id,
        amount=price,
    )

    db.session.add(offer)

    # Commit and roll back if there's a database error
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f"IntegrityError: {e}")
        return error_response("Failed to create offer.", ErrorType.BAD_REQUEST)

    # Create notification for the new offer (user)
    notification_user = Notification(
        type=NotificationTypeEnum.NEW_OFFER,
        message=f"You made a new offer for ${price:.2f}!",
        user_id=user.id,
        question_id=question.id,
    )
    db.session.add(notification_user)
    db.session.commit()

    # Create notification for the new offer (question author)
    notification_author = Notification(
        type=NotificationTypeEnum.NEW_OFFER,
        message=f"You have a new offer from {user.username} for ${price:.2f}!",
        user_id=question.user_id,
        question_id=question.id,
    )
    db.session.add(notification_author)
    db.session.commit()

    # after committing offer, we want to push to the question author’s room:
    question_author_id = question.user_id
    room_name = f"user_{question_author_id}"

    # socketio emission! this sends a real time notification to the author
    socketio.emit(
        "new_offer",
        {
            "question_id": question.id,
            "offer_id": offer.id,
            "offer_amount": offer.amount,
            "message": f"You have a new offer from {user.username} for ${price:.2f}!",
        },
        room=room_name,
    )

    response = jsonify(offer.to_dict(simplified=True))

    return (response, HTTPStatus.CREATED)


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

    offer = db.session.query(Offer).filter_by(id=id_offer).first()

    # If no offer is found, return an error response
    if not offer:
        return error_response("Offer not found", ErrorType.NOT_FOUND)

    return jsonify(offer.to_dict()), HTTPStatus.OK


# Endpoint: /backend/offer/<int:id_offer>
@offer.route("/<int:id_offer>", methods=["PUT"])
@jwt_required()
@use_args(
    {
        "amount": fields.Float(required=True),
    }
)
def update_offer(args, id_offer: int) -> flask_typing.ResponseReturnValue:
    """
    Update an offer price

    Args:
        args (dict): The arguments containing the new price.
        id_offer (int): The ID of the offer to be updated.

    Returns:
        flask_typing.ResponseReturnValue: The updated offer details.
    """

    offer = db.session.query(Offer).filter_by(id=id_offer).first()

    # If no offer is found, return an error response
    if not offer:
        return error_response("Offer not found", ErrorType.NOT_FOUND)

    user = get_current_user()

    # Check if user exists
    if not user:
        return error_response("User does not exist", ErrorType.USER_NOT_FOUND)

    # Check user is author of the question or owner of the offer
    if not (offer.user_id == user.id):
        return error_response(
            "User is not owner of the offer",
            ErrorType.UNAUTHORIZED,
        )

    # Check if offer is active
    if not offer.active:
        return error_response("Offer is not active", ErrorType.BAD_REQUEST)

    # Check that offer status is SENT
    if not offer.status == OfferStatusEnum.SENT:
        return error_response("Offer status is not SENT", ErrorType.BAD_REQUEST)

    # Update offer fields from args
    if not (offer.question.price <= args["amount"] <= 2 * offer.question.price):
        return error_response("Invalid offer amount", ErrorType.BAD_REQUEST)

    offer.amount = args["amount"]

    # Try adding to database
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f"IntegrityError: {e}")
        return error_response("Couldn't update offer", ErrorType.BAD_REQUEST)

    amount = offer.amount
    # Create notification for the updated offer (user)
    notification_user = Notification(
        type=NotificationTypeEnum.UPDATED_OFFER,
        message=f"You changed the offer amount to ${amount:.2f}!",
        user_id=offer.user_id,
        question_id=offer.question.id,
    )
    db.session.add(notification_user)
    db.session.commit()

    # Create notification for the updated offer (question author)
    notification_author = Notification(
        type=NotificationTypeEnum.UPDATED_OFFER,
        message=f"{offer.user.username} changed their offer to ${amount:.2f}!",
        user_id=offer.question.user_id,
        question_id=offer.question.id,
    )
    db.session.add(notification_author)
    db.session.commit()

    return jsonify(offer.to_dict()), HTTPStatus.OK


# Endpoint: /backend/offer/<int:id_offer>
@offer.route("/<int:id_offer>", methods=["DELETE"])
@jwt_required()
def delete_offer(id_offer: int) -> flask_typing.ResponseReturnValue:
    """
    Delete an offer from the database.

    Args:
        id_offer (int): The ID of the offer to be deleted.

    Returns:
        flask_typing.ResponseReturnValue: The response value indicating the success or failure of the deletion.
    """

    user = get_current_user()

    offer = db.session.query(Offer).filter_by(id=id_offer).first()

    # If no offer is found, return an error response
    if not offer:
        return error_response("Offer not found", ErrorType.NOT_FOUND)

    if not offer.user_id == user.id:
        return error_response(
            "User not permited to delete offer", ErrorType.UNAUTHORIZED
        )

    # Check that offer status is SENT
    if not offer.status == OfferStatusEnum.SENT:
        return error_response("Offer status is not SENT", ErrorType.BAD_REQUEST)

    offer.status = OfferStatusEnum.REMOVED
    offer.active = False

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f"IntegrityError: {e}")
        return error_response("Couldn't delete offer", ErrorType.BAD_REQUEST)

    # Create notification for the updated offer (user)
    notification_user = Notification(
        type=NotificationTypeEnum.OFFER_REVOKED,
        message=f"You revoked an offer to {offer.question.user.username}!",
        user_id=offer.user_id,
        question_id=offer.question.id,
    )
    db.session.add(notification_user)
    db.session.commit()

    # Create notification for the updated offer (question author)
    notification_author = Notification(
        type=NotificationTypeEnum.OFFER_REVOKED,
        message=f"{offer.user.username} revoked their offer!",
        user_id=offer.question.user_id,
        question_id=offer.question.id,
    )
    db.session.add(notification_author)
    db.session.commit()

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
        flask_typing.ResponseReturnValue: The response containing the offers associated with the user.
    """

    user = get_current_user()

    # Check if user exists
    if not user:
        return error_response("User does not exist", ErrorType.USER_NOT_FOUND)

    offers = Offer.query.filter_by(user_id=user_id, active=True).all()
    return jsonify(Offer.to_dict_all(offers)), HTTPStatus.OK


# Endpoint: /backend/offer/accept/<int:offer_id>
@offer.route("/accept/<int:offer_id>", methods=["POST"])
@jwt_required()
def accept_offer(offer_id: int) -> flask_typing.ResponseReturnValue:
    """
    Accept an offer for a question.

    Args:
        offer_id (int): The ID of the offer to accept.

    Returns:
        flask_typing.ResponseReturnValue: The response containing the accepted offer.
    """

    user = get_current_user()

    # Check if user exists
    if not user:
        return error_response("User does not exist", ErrorType.USER_NOT_FOUND)

    offer = db.session.query(Offer).filter_by(id=offer_id).first()

    # If no offer is found, return an error response
    if not offer:
        return error_response("Offer not found", ErrorType.NOT_FOUND)

    question = db.session.query(Question).filter_by(id=offer.question_id).first()

    # Check if question exists
    if not question:
        return error_response("Question does not exist", ErrorType.NOT_FOUND)

    # Check if user is author of the question
    if not question.user_id == user.id:
        return error_response(
            "User is not author of the question", ErrorType.UNAUTHORIZED
        )

    # Check if question is visible and unsolved
    if question.solved:
        return error_response("Question is already solved", ErrorType.BAD_REQUEST)
    if not question.visible:
        return error_response("Question is not visible", ErrorType.BAD_REQUEST)

    # Check if offer is active
    if not offer.active:
        return error_response("Offer is not active", ErrorType.BAD_REQUEST)

    # Check if offer is not already accepted
    if offer.status == OfferStatusEnum.ACCEPTED:
        return error_response("Offer is already accepted", ErrorType.BAD_REQUEST)

    # Check if offer has already been declined
    if offer.status == OfferStatusEnum.DECLINED:
        return error_response("Offer is already declined", ErrorType.BAD_REQUEST)

    # Check that offer status is SENT
    if not offer.status == OfferStatusEnum.SENT:
        return error_response("Offer status is not SENT", ErrorType.BAD_REQUEST)

    # Update offer status to accepted
    offer.status = OfferStatusEnum.ACCEPTED

    # Get other offers for same question, decline them and make them inactive
    other_offers_for_question = (
        db.session.query(Offer)
        .filter(Offer.question_id == question.id)
        .filter(Offer.id != offer_id)
        .filter(Offer.active == True)
        .all()
    )

    for other_offer in other_offers_for_question:
        other_offer.status = OfferStatusEnum.DECLINED
        other_offer.active = False

    # Set question to solved after an offer has been accepted
    question.solved = True

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f"IntegrityError: {e}")
        return error_response("Couldn't accept offer", ErrorType.BAD_REQUEST)

    # Create notification for the updated offer (user)
    notification_user = Notification(
        type=NotificationTypeEnum.OFFER_ACCEPTED,
        message=f"Your offer to {offer.question.user.username} was accepted! Check the question information as soon as possible to get in touch with them.",
        user_id=offer.user_id,
        question_id=offer.question.id,
    )
    db.session.add(notification_user)
    db.session.commit()

    # Create notification for the updated offer (question author)
    notification_author = Notification(
        type=NotificationTypeEnum.OFFER_ACCEPTED,
        message=f"You accepted {offer.user.username}'s offer! Check the question information as soon as possible to get in touch with them.",
        user_id=offer.question.user_id,
        question_id=offer.question.id,
    )
    db.session.add(notification_author)
    db.session.commit()

    for other_offer in other_offers_for_question:
        # Create notification for the other offers rejeted
        notification_declined = Notification(
            type=NotificationTypeEnum.OFFER_DECLINED,
            message=f"Your offer to {offer.question.user.username} was declined!",
            user_id=other_offer.user_id,
            question_id=offer.question.id,
        )
        db.session.add(notification_declined)
        db.session.commit()

    return jsonify(offer.to_dict()), HTTPStatus.OK


# Endpoint: /backend/offer/decline/<int:offer_id>
@offer.route("/decline/<int:offer_id>", methods=["POST"])
@jwt_required()
def decline_offer(offer_id: int) -> flask_typing.ResponseReturnValue:
    """
    Decline an offer for a question.
    Args:
        offer_id (int): The ID of the offer to decline.
    Returns:
        flask_typing.ResponseReturnValue: The response containing the declined offer.
    """

    user = get_current_user()

    # Check if user exists
    if not user:
        return error_response("User does not exist", ErrorType.USER_NOT_FOUND)

    offer = db.session.query(Offer).filter_by(id=offer_id).first()

    # If no offer is found, return an error response
    if not offer:
        return error_response("Offer not found", ErrorType.NOT_FOUND)

    question = db.session.query(Question).filter_by(id=offer.question_id).first()

    # Check if question exists
    if not question:
        return error_response("Question does not exist", ErrorType.NOT_FOUND)

    # Check if user is author of the question
    if not question.user_id == user.id:
        return error_response(
            "User is not author of the question", ErrorType.UNAUTHORIZED
        )

    # Check if question is visible and unsolved
    if question.solved:
        return error_response("Question is already solved", ErrorType.BAD_REQUEST)
    if not question.visible:
        return error_response("Question is not visible", ErrorType.BAD_REQUEST)

    # Check if offer is active
    if not offer.active:
        return error_response("Offer is not active", ErrorType.BAD_REQUEST)

    # Check if offer is not already declined
    if offer.status == OfferStatusEnum.DECLINED:
        return error_response("Offer is already declined", ErrorType.BAD_REQUEST)

    # Check that offer status is SENT
    if not offer.status == OfferStatusEnum.SENT:
        return error_response("Offer status is not SENT", ErrorType.BAD_REQUEST)

    # Update offer status to DECLINED
    offer.status = OfferStatusEnum.DECLINED

    # Make offer inactive
    offer.active = False

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f"IntegrityError: {e}")
        return error_response("Couldn't decline offer", ErrorType.BAD_REQUEST)

    # Create notification for the updated offer (user)
    notification_user = Notification(
        type=NotificationTypeEnum.OFFER_DECLINED,
        message=f"Your offer to {offer.question.user.username} was declined!",
        user_id=offer.user_id,
        question_id=offer.question.id,
    )
    db.session.add(notification_user)
    db.session.commit()

    # Create notification for the updated offer (question author)
    notification_author = Notification(
        type=NotificationTypeEnum.OFFER_DECLINED,
        message=f"You declined {offer.user.username}'s offer!",
        user_id=offer.question.user_id,
        question_id=offer.question.id,
    )
    db.session.add(notification_author)
    db.session.commit()

    return jsonify(offer.to_dict()), HTTPStatus.OK
