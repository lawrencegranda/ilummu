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
from edify.models import User, Offer, Question, Method, Course
from edify.utils.constants import OfferStatusEnum

# Initialize Faker for generating fake data
fake = Faker()


class TestCreateOffer:

    def test_create_offer_success(self, client_with_question, user_jwt):
        """
        Test creating an offer successfully.
        """
        user, jwt = user_jwt

        question = (
            db.session.query(Question)
            .filter(Question.user_id != user.id)
            .filter(Question.visible == True)
            .filter(Question.solved == False)
            .first()
        )

        question_id = question.id
        price = 1.5 * question.price

        response = client_with_question.post(
            url_for("backend.offer.create_offer"),
            json={"question_id": question_id, "price": price},
            headers=jwt,
        )

        assert response.status_code == HTTPStatus.CREATED, response.json

        response = response.get_json()

        assert "offer" in response

        offer = response.get("offer")

        assert "id" in offer, "Offer has no id"

        offer = db.session.query(Offer).filter(Offer.id == offer["id"]).first()
        assert offer, "Offer not found in database"

        assert offer.user_id == user.id, f"User ID does not match {offer.user_id}"

    def test_create_offer_invalid_question(self, client_with_question, user_jwt):
        """
        Test creating an offer with an invalid question ID.
        """
        user, jwt = user_jwt

        response = client_with_question.post(
            url_for("backend.offer.create_offer"),
            json={"question_id": -1, "price": 10},
            headers=jwt,
        )

        assert response.status_code == HTTPStatus.NOT_FOUND, response.json

        assert response.get_json()["msg"] == "Question does not exist"

    def test_create_offer_existing_offer(self, client_with_question, user_jwt):
        """
        Test creating an offer when the user has already made an offer.
        """
        user, jwt = user_jwt

        question = (
            db.session.query(Question)
            .filter(Question.user_id != user.id)
            .filter(Question.visible == True)
            .filter(Question.solved == False)
            .first()
        )

        question_id = question.id
        price = 1.5 * question.price

        offer = Offer(
            user_id=user.id,
            question_id=question_id,
            amount=price,
        )

        db.session.add(offer)
        db.session.commit()

        response = client_with_question.post(
            url_for("backend.offer.create_offer"),
            json={"question_id": question_id, "price": price},
            headers=jwt,
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        assert response.get_json()["msg"] == "User already made offer to question"

    def test_create_offer_not_visible_question(self, client_with_question, user_jwt):
        """
        Test creating an offer when the question is not visible.
        """
        user, jwt = user_jwt

        question = (
            db.session.query(Question)
            .filter(Question.user_id != user.id)
            .filter(Question.visible == True)
            .filter(Question.solved == False)
            .first()
        )

        question.visible = False
        db.session.commit()

        assert question, "User cannot create Offer for any question in database"

        question_id = question.id
        price = 1.5 * question.price

        response = client_with_question.post(
            url_for("backend.offer.create_offer"),
            json={"question_id": question_id, "price": price},
            headers=jwt,
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        assert response.get_json()["msg"] == "Question is not visible"

    def test_create_offer_solved_question(self, client_with_question, user_jwt):
        """
        Test creating an offer when the question is already solved.
        """
        user, jwt = user_jwt

        question = (
            db.session.query(Question)
            .filter(Question.user_id != user.id)
            .filter(Question.solved == False)
            .filter(Question.visible == True)
            .first()
        )

        question.solved = True
        db.session.commit()
        
        db.session.commit()

        assert question, "User cannot create Offer for any question in Database"

        question_id = question.id
        price = 1.5 * question.price

        response = client_with_question.post(
            url_for("backend.offer.create_offer"),
            json={"question_id": question_id, "price": price},
            headers=jwt,
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        assert response.get_json()["msg"] == "Question is already solved"


class TestGetOffer:

    def test_get_offer_success(self, client_with_offer, user_jwt):
        """
        Test getting an offer successfully.
        """
        user, jwt = user_jwt

        offer = db.session.query(Offer).first()

        assert offer, "User does not have any offer in Database"

        response = client_with_offer.get(
            url_for("backend.offer.get_offer", id_offer=offer.id), headers=jwt
        )

        assert response.status_code == HTTPStatus.OK, response.json

        offer = response.get_json()

        assert offer, "Offer not found in database"

    def test_get_offer_invalid_id_offer(self, client_with_offer, user_jwt):
        """
        Test getting an offer with an invalid offer ID.
        """
        user, jwt = user_jwt

        response = client_with_offer.get(
            url_for("backend.offer.get_offer", id_offer=0), headers=jwt
        )

        assert response.status_code == HTTPStatus.NOT_FOUND, response.json

        # Assert right error message is returned.
        assert (
            "msg" in response.get_json()
            and "Offer not found" in response.get_json()["msg"]
        ), response.get_json()
