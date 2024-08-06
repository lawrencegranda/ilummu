# Standard Library imports
from http import HTTPStatus
from typing import Optional, Any, Tuple

# Third-Party Framework imports
from flask import Blueprint, Flask, jsonify
from flask import typing as flask_typing
from flask_jwt_extended import jwt_required
from webargs import fields, validate
from webargs.flaskparser import use_args

# Local Application imports
from edify import db
from edify.models import (
    User,
    Question,
    Offer,
    OfferStatus,
)
from edify.utils.constants import ErrorType
from edify.backend.user.utils import (
    get_current_user
    )
from edify.utils.utils import (
    error_response
)
from edify.utils.constants import (
    ErrorType
)

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
        "price": fields.Float(required=False),
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
    question = db.session.query(Question).filter_by(id = question_id).first()
    if not question:
        return error_response("Question does not exist", ErrorType.NOT_FOUND)
    
    # Check if user has made an unresolved offer to question
    existing_offer = db.session.query(Offer).filter_by(question_id = question_id, user_id = user.id).first()
    if existing_offer and existing_offer.active:
        return error_response("User already made offer to question", ErrorType.BAD_REQUEST)
    
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
        user_id = user.id,
        question_id = question.id,
        amount = price,
    )
    
    db.session.add(offer)
    db.session.commit()
    
    response = jsonify({"offer": offer.to_dict(simplified = True)})
    return (response, HTTPStatus.CREATED)
