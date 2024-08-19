# Standard Library imports
from http import HTTPStatus
from typing import Optional, Any, Tuple

# Third-Party Framework imports
from flask import Blueprint, Flask, jsonify, redirect, url_for
from flask import typing as flask_typing
from flask_jwt_extended import jwt_required
from webargs import fields, validate
from webargs.flaskparser import use_args

# Local Application imports
from edify import db
from edify.models import User, Question, Offer, OfferStatus, Notification
from edify.utils.constants import ErrorType
from edify.backend.user.utils import get_current_user
from edify.utils.utils import error_response
from edify.utils.constants import ErrorType, NotificationTypeEnum

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
    Make a new offer and post it in the databse

    Parameters:
        pass

    Returns:
        pass
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
        .filter_by(question_id=question_id, user_id=user.id)
        .first()
    )
    if existing_offer and existing_offer.active:
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
    except IntegrityError:
        db.session.rollback()
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

    response = jsonify({"offer": offer.to_dict(simplified=True)})
    return (response, HTTPStatus.CREATED)


# Endpoint: /backend/offer/<int:id_offer>
@offer.route("/<int:id_offer>", methods=["GET"])
@jwt_required()
def get_offer(id_offer: int) -> flask_typing.ResponseReturnValue:
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
        "status": fields.String(required=False),
        "active": fields.Boolean(required=False),
    }
)
def update_offer(args, id_offer: int) -> flask_typing.ResponseReturnValue:
    offer = db.session.query(Offer).filter_by(id=id_offer).first()

    # If no offer is found, return an error response
    if not offer:
        return error_response("Offer not found", ErrorType.NOT_FOUND)

    # Update offer fields from args
    offer.amount = args["amount"]
    if "status" in args:
        offer.status = args["status"]
    if "active" in args:
        offer.active = args["active"]
    db.session.commit()

    # Create notification for the updated offer (user)
    notification_user = Notification(
        type=NotificationTypeEnum.UPDATED_OFFER,
        message=f"You changed the offer amount to ${amount:.2f}!",
        user_id=offer.user.id,
        question_id=question.id,
    )
    db.session.add(notification_user)
    db.session.commit()

    # Create notification for the updated offer (question author)
    notification_author = Notification(
        type=NotificationTypeEnum.NEW_OFFER,
        message=f"{offer.user.username} changed their offer to ${amount:.2f}!",
        user_id=question.user_id,
        question_id=question.id,
    )
    db.session.add(notification_author)
    db.session.commit()

    return jsonify(offer.to_dict()), HTTPStatus.OK


# Endpoint: /backend/offer/<int:id_offer>
@offer.route("/<int:id_offer>", methods=["DELETE"])
@jwt_required()
def delete_offer(id_offer: int) -> flask_typing.ResponseReturnValue:
    offer = db.session.query(Offer).filter_by(id=id_offer).first()

    # If no offer is found, return an error response
    if not offer:
        return error_response("Offer not found", ErrorType.NOT_FOUND)

    # Not implemented
    return error_response(
        "Not Implemented but passed checks.", ErrorType.NOT_IMPLEMENTED
    )

    # Set offer status to REMOVED (i think)
    db.session.commit()
    return jsonify({"msg": "Offer deleted"}), HTTPStatus.NO_CONTENT


# Endpoint: /backend/offer/user/<int:user_id>
@offer.route("/user/<int:user_id>", methods=["GET"])
@jwt_required()
def get_offers_by_user(user_id: int) -> flask_typing.ResponseReturnValue:
    user = get_current_user()
    # Check if user exists
    if not user:
        return error_response("User does not exist", ErrorType.USER_NOT_FOUND)

    offers = Offer.query.filter_by(user_id=user_id).all()
    return jsonify(Offer.to_dict_all(offers)), HTTPStatus.OK
