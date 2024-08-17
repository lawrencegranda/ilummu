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

        all_questions = db.session.query(Question).all()
        question = None
        for q in all_questions:
            if q.user_id == user.id and not q.solved and q.visible:
                question = q
                break
        
        assert question, "User cannot create Offer for any question in Database"
        
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
        
        assert "offer" in response
        
        offer = response.get_json().get("offer")
        assert "id" in offer, "Offer has no id"
        
        offer = db.session.get(Offer, offer["id"])
        assert offer, "Offer not found in database"
        
        assert offer.user_id == user.id, f"User ID does not match {offer.user_id}"
        
        assert offer.question_id == question.id, f"Question ID does not match {offer.question_id}"
        assert offer.active, "Offer not active"
        assert offer.amount, "Amount must not be null"
        assert offer.status == OfferStatusEnum.SENT, "Newly created offer must have status 'SENT'"
        
        
    def test_create_offer_invalid_question(self, client_with_data, user_jwt):
        """
        Test creating an offer with an invalid question ID.
        """
        user, jwt = user_jwt
        
        response = client_with_data.post(
            url_for("backend.offer.create_offer"),
            json = {
                "question_id": -1,
                "price": 10
            },
            headers = jwt
        )
        
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
        
        assert response.get_json() == {"error": "Question does not exist"}
        
        
    def test_create_offer_low_price(self, client_with_data, user_jwt):
        """
        Test creating an offer with a price lower than the question's price.
        """
        user, jwt = user_jwt

        all_questions = db.session.query(Question).all()
        question = None
        for q in all_questions:
            if q.user_id == user.id and not q.solved and q.visible:
                question = q
                break
        
        assert question, "User cannot create Offer for any question in Database"
        
        question_id = question.id
        price = 0.5 * question.price
        
        response = client_with_data.post(
            url_for("backend.offer.create_offer"),
            json = {
                "question_id": question_id,
                "price": price
            },
            headers = jwt
        )
        
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
        
        assert response.get_json() == {"error": "Price is too low"}
        
    
    def test_create_offer_high_price(self, client_with_data, user_jwt):
        """
        Test creating an offer with a price higher than twice the question's price.
        """
        user, jwt = user_jwt

        all_questions = db.session.query(Question).all()
        question = None
        for q in all_questions:
            if q.user_id == user.id and not q.solved and q.visible:
                question = q
                break
        
        assert question, "User cannot create Offer for any question in Database"
        
        question_id = question.id
        price = 2.5 * question.price
        
        response = client_with_data.post(
            url_for("backend.offer.create_offer"),
            json = {
                "question_id": question_id,
                "price": price
            },
            headers = jwt
        )
        
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
        
        assert response.get_json() == {"error": "Price is too high"}
        
        
    def test_create_offer_already_made(self, client_with_data, user_jwt):
        """
        Test creating an offer when an offer has already been made to the question.
        """
        user, jwt = user_jwt

        all_questions = db.session.query(Question).all()
        question = None
        for q in all_questions:
            if q.user_id == user.id and not q.solved and q.visible:
                question = q
                break
        
        assert question, "User cannot create Offer for any question in Database"
        
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
        
        response = client_with_data.post(
            url_for("backend.offer.create_offer"),
            json = {
                "question_id": question_id,
                "price": price
            },
            headers = jwt
        )
        
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
        
        assert response.get_json() == {"error": "User already made offer to question"}
        
        
    def test_create_offer_not_visible_question(self, client_with_data, user_jwt):
        """
        Test creating an offer when the question is not visible.
        """
        user, jwt = user_jwt

        all_questions = db.session.query(Question).all()
        question = None
        for q in all_questions:
            if q.user_id == user.id and not q.solved and not q.visible:
                question = q
                break
        
        assert question, "User cannot create Offer for any question in Database"
        
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
        
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
        
        assert response.get_json() == {"error": "Question is not visible"}
        
        
    def test_create_offer_solved_question(self, client_with_data, user_jwt):
        """
        Test creating an offer when the question is already solved.
        """
        user, jwt = user_jwt

        all_questions = db.session.query(Question).all()
        question = None
        for q in all_questions:
            if q.user_id == user.id and q.solved and q.visible:
                question = q
                break
        
        assert question, "User cannot create Offer for any question in Database"
        
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
        
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
        
        assert response.get_json() == {"error": "Question is already solved"}
        
        
class TestGetOffer:
    
        def test_get_offer_success(self, client_with_data, user_jwt):
            """
            Test getting an offer successfully.
            """
            user, jwt = user_jwt
    
            all_offers = db.session.query(Offer).all()
            offer = None
            for o in all_offers:
                if o.user_id == user.id:
                    offer = o
                    break
            
            assert offer, "User does not have any offer in Database"
            
            response = client_with_data.get(
                url_for("backend.offer.get_offer", offer_id = offer.id),
                headers = jwt
            )
            
            assert response.status_code == HTTPStatus.OK, response.json
            
            offer = response.get_json()
            
            assert offer, "Offer not found in database"
            
            assert offer.user_id == user.id, f"User ID does not match {offer.user_id}"
            
            
        def test_get_offer_invalid_offer_id(self, client_with_data, user_jwt):
            """
            Test getting an offer with an invalid offer ID.
            """
            user, jwt = user_jwt
            
            response = client_with_data.get(
                url_for("backend.offer.get_offer", offer_id = -1),
                headers = jwt
            )
            
            assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
            
            assert response.get_json() == {"error": "Offer not found"}
            
            
        def test_get_offer_not_made(self, client_with_data, user_jwt):
            """
            Test getting an offer that the user has not made.
            """
            user, jwt = user_jwt
    
            all_offers = db.session.query(Offer).all()
            offer = None
            for o in all_offers:
                if o.user_id != user.id:
                    offer = o
                    break
            
            assert offer, "User cannot get Offer from Database"
            
            response = client_with_data.get(
                url_for("backend.offer.get_offer", offer_id = offer.id),
                headers = jwt
            )
            
            assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
            
            assert response.get_json() == {"error": "User did not make offer"}