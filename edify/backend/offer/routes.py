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
from edify.backend.user.utils import get_current_user

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

    pass


# Endpoint: /backend/offer/<int:offer_id>
@offer.route("/<int:offer_id>", methods=["GET"])
@jwt_required()
def get_offer(offer_id: int) -> flask_typing.ResponseReturnValue:
    offer = Offer.query.get_or_404(offer_id)
    return jsonify(offer.to_dict()), HTTPStatus.OK


# Endpoint: /backend/offer/<int:offer_id>
@offer.route("/<int:offer_id>", methods=["PUT"])
@jwt_required()
@use_args(
    {
        "amount": fields.Float(required=True),
        "status": fields.String(required=False),
        "active": fields.Boolean(required=False),
    }
)
def update_offer(args, offer_id: int) -> flask_typing.ResponseReturnValue:
    offer = Offer.query.get_or_404(offer_id)
    # Update offer fields from args
    offer.amount = args["amount"]
    if "status" in args:
        offer.status = args["status"]
    if "active" in args:
        offer.active = args["active"]
    db.session.commit()
    return jsonify(offer.to_dict()), HTTPStatus.OK


# Endpoint: /backend/offer/<int:offer_id>
@offer.route("/<int:offer_id>", methods=["DELETE"])
@jwt_required()
def delete_offer(offer_id: int) -> flask_typing.ResponseReturnValue:
    offer = Offer.query.get_or_404(offer_id)
    db.session.delete(offer)
    db.session.commit()
    return jsonify({"message": "Offer deleted"}), HTTPStatus.NO_CONTENT


# Endpoint: /backend/offer/question/<int:question_id>
@offer.route("/question/<int:question_id>", methods=["GET"])
@jwt_required()
def get_offers_by_question(question_id: int) -> flask_typing.ResponseReturnValue:
    offers = Offer.query.filter_by(question_id=question_id).all()
    return jsonify(Offer.to_dict_all(offers)), HTTPStatus.OK


# Endpoint: /backend/offer/user/<int:user_id>
@offer.route("/user/<int:user_id>", methods=["GET"])
@jwt_required()
def get_offers_by_user(user_id: int) -> flask_typing.ResponseReturnValue:
    offers = Offer.query.filter_by(user_id=user_id).all()
    return jsonify(Offer.to_dict_all(offers)), HTTPStatus.OK
