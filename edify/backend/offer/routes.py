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
