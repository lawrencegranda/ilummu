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

    # LAWRENCE: you need to create a fixture. Right now you have no questions, this is
    # because the database is a mock sqlite instance that is brand new and empty.
    # Create a fixture in conftest.py where you create a question that you use to test against.

    def test_create_offer_success(self, client_with_question, user_jwt):
        """
        Test creating an offer successfully.
        """
        user, jwt = user_jwt

        # LAWRENCE: instead, filter the query.
        question = (
            db.session.query(Question)
            .filter(Question.user_id != user.id)
            .filter(Question.visible == True)
            .first()
        )

        # question = db.session.query(Question).first()
        # while question.user_id == user.id or question.solved or not question.visible:
        #     question = db.session.query(
        #         Question
        #     ).first()  # you are getting the same question every time, infinite loop

        question_id = question.id
        price = 1.5 * question.price

        response = client_with_question.post(
            url_for("backend.offer.create_offer"),
            json={"question_id": question_id, "price": price},
            headers=jwt,
        )

        assert response.status_code == HTTPStatus.CREATED, response.json

        offer = response.get_json()

        assert "id" in offer, "Offer has no id"

        offer = db.session.get(Offer, offer["id"])
        assert offer, "Offer not found in database"

        assert offer.user_id == user.id, f"User ID does not match {offer.user_id}"

        assert (
            offer.question_id == question.id
        ), f"Question ID does not match {offer.question_id}"
        assert offer.active, "Offer not active"
        assert offer.amount, "Amount must not be null"
        assert (
            offer.status == OfferStatusEnum.SENT
        ), "Newly created offer must have status 'SENT'"

    def test_create_question_user_not_found(self, client_with_data, user_jwt):
        """
        Test creating a question without a user (Unauthorized).
        """
        user, jwt = user_jwt

        method = db.session.query(Method).first()

        course = db.session.query(Course).filter_by(school_id=user.school_id).first()
        academic_field = course.academic_field

        response = client_with_data.post(
            url_for("backend.question.create_question"),
            json={
                "class_code": course.code,
                "class_name": course.name,
                "academic_field": academic_field.value,
                "method": method.value,
                "solve_time": 30,
                "price": 10.0,
                "request_message": "What is Python?",
            },
            headers=None,
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json

    def test_create_question_invalid_method(self, client_with_data, user_jwt):
        """
        Test creating a question with an invalid method ID.
        """
        user, jwt = user_jwt

        invalid_method = "none"  # Assuming this method does not exist

        course = db.session.query(Course).filter_by(school_id=user.school_id).first()
        academic_field = course.academic_field

        response = client_with_data.post(
            url_for("backend.question.create_question"),
            json={
                "class_code": course.code,
                "class_name": course.name,
                "academic_field": academic_field.value,
                "method": invalid_method,
                "solve_time": 30,
                "price": 10.0,
                "request_message": "What is Python?",
            },
            headers=jwt,
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
        assert "Invalid method" in response.get_json()["msg"]

    def test_create_question_invalid_academic_field(self, client_with_data, user_jwt):
        """
        Test creating a question with an invalid academic field.
        """
        user, jwt = user_jwt

        method = db.session.query(Method).first()

        course = db.session.query(Course).filter_by(school_id=user.school_id).first()
        invalid_academic_field = "Invalid"

        response = client_with_data.post(
            url_for("backend.question.create_question"),
            json={
                "class_code": course.code,
                "class_name": course.name,
                "academic_field": invalid_academic_field,
                "method": method.value,
                "solve_time": 30,
                "price": 10.0,
                "request_message": "What is Python?",
            },
            headers=jwt,
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
        assert "Invalid academic field" in response.get_json()["msg"]
