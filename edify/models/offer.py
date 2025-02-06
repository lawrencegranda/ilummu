"""Offer-related models."""

# Standard Library imports
from datetime import datetime
from typing import Dict, Any

# Third-Party Framework imports
from sqlalchemy import Index, event
from sqlalchemy.orm import Session

# Local Application imports
from edify.core import db
from edify.models.base import BaseModel
from edify.utils.constants import OfferStatusEnum
from edify.utils.utils import date_to_int


class OfferStatus(BaseModel):
    """
    Table that stores the status of offers/questions.
    """

    value = db.Column(db.String(50), unique=True, nullable=False, primary_key=True)

    def __repr__(self):
        return f"OfferStatus({self.value})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        return {
            "value": self.value,
        }

    @staticmethod
    def validator(_mapper, _connection, target):
        """Validate offer status value before insert/update."""
        if not target.value in OfferStatusEnum.values():
            raise ValueError(f'OFFER STATUS MODEL: Invalid value ("{target.value}").')


# Attach event listeners
event.listen(OfferStatus, "before_insert", OfferStatus.validator)
event.listen(OfferStatus, "before_update", OfferStatus.validator)


class Offer(BaseModel):
    """
    Table that contains offer information

    Entries are created when a user offers to help solve a question.
    Entries are updated when the offer status changes.
    """

    __table_args__ = (
        Index("ix_offer_question_id", "question_id"),
        Index("ix_offer_user_id", "user_id"),
    )

    # Primary key that identifies the offer
    id = db.Column(db.Integer, primary_key=True)

    # User who made the offer
    # Many-to-One relationship with User model
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref="offers", lazy=True)

    # Question associated with the offer
    # Many-to-One relationship with Question model
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    question = db.relationship("Question", backref="offers", lazy=True)

    # Amount offered
    amount = db.Column(db.Float, nullable=False)

    # Whether the offer is active
    active = db.Column(db.Boolean, nullable=False, default=True)

    # Status of the offer
    status = db.Column(
        db.String(30),
        db.ForeignKey("offer_status.value"),
        nullable=False,
        default=OfferStatusEnum.SENT,
    )

    # Entry creation date (to keep track)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Entry updated date (to keep track)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Offer({self.id}, {self.question_id}, {self.amount}, {self.status}, {self.active})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "question_id": self.question_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "status": self.status,
            "active": self.active,
            "created_at": date_to_int(self.created_at),
            "updated_at": date_to_int(self.updated_at),
        }

        if not simplified:
            result["user"] = self.user.to_dict(simplified=False)

        return result

    @staticmethod
    def validator(_mapper, _connection, target: "Offer"):
        """Validate offer data, including active status and uniqueness constraints."""
        # Fill in default values
        if target.active is None:
            target.active = True
        if target.status is None:
            target.status = OfferStatusEnum.SENT

        # Ensure amount is positive
        if target.amount <= 0:
            raise ValueError(
                f'OFFER MODEL: Amount must be a positive value ("{target.amount}").'
            )

        # Ensure created_at is before updated_at
        if target.updated_at and target.updated_at < target.created_at:
            raise ValueError(
                f'OFFER MODEL: Creation ("{target.created_at}") must be '
                f'before update ("{target.updated_at}").'
            )

        # Enforce that if the offer is inactive, it cannot have an active status
        if target.status in OfferStatusEnum.inactive and target.active:
            raise ValueError(
                f'OFFER MODEL: Offer status is inactive ("{target.status}") but still active).'
            )

        # Enforce that if the offer is not active, it must have an inactive status
        if not target.active and not target.status in OfferStatusEnum.inactive:
            raise ValueError(
                f'OFFER MODEL: Offer is not active but status is not inactive ("{target.status}").'
            )

        # Ensure only one active offer per user and question
        if target.active:
            sess = Session.object_session(target)

            # Check if any other active offers exist for this user and question
            existing_offer = (
                sess.query(Offer)
                .filter(
                    Offer.user_id == target.user_id,
                    Offer.question_id == target.question_id,
                    Offer.active.is_(True),
                    Offer.id != target.id,
                )
                .first()
            )

            if existing_offer:
                raise ValueError(
                    f"OFFER MODEL: Only one active offer per user and question is allowed. "
                    f"User: {target.user_id}, Question: {target.question_id}."
                )


# Attach event listeners
event.listen(Offer, "before_insert", Offer.validator)
event.listen(Offer, "before_update", Offer.validator)
