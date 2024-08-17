# Standard Library imports
from http import HTTPStatus
import datetime

# Third-Party Framework imports
from faker import Faker
from flask import Flask, url_for
from flask_jwt_extended import create_access_token
import pytest

# Local Application imports
from edify import db
from edify.models import User, Offer, Question
from edify.utils.constants import OfferStatusEnum

# Initialize Faker for generating fake data
fake = Faker()


class TestCreateOffer:

    def test_create_offer_success(self, client_with_data, user_jwt):
        """
        Test creating an offer successfully.
        """
        user, jwt = user_jwt

        question = db.session.query(Question).first()
        while question.user_id == user.id or question.solved or not question.visible:
            question = db.session.query(Question).first()
        
        question_id = question.id
        price = 1.5 * question.price
        
        response = client_with_data.post(
            url_for("backend.offer.create_offer"),
            json = {
                "question_id": question_id,
                "price": price
            },
            headers = jwt
        )
        
        assert response.status_code == HTTPStatus.CREATED, response.json
        
        offer = response.get_json().get("offer")
        assert "id" in offer, "Offer has no id"
        
        offer = db.session.get(Offer, offer["id"])
        assert offer, "Offer not found in database"
        
        assert offer.user_id == user.id, f"User ID does not match {offer.user_id}"
        
        assert offer.question_id == question.id, f"Question ID does not match {offer.question_id}"
        assert offer.active, "Offer not active"
        assert offer.amount, "Amount must not be null"
        assert offer.status == OfferStatusEnum.SENT, "Newly created offer must have status 'SENT'"
        
        
    