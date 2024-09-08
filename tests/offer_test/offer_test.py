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
from edify.models import User, Offer, Question, Method, Course, Notification
from edify.utils.constants import OfferStatusEnum, primitives
from tests.utils import get_jwt_header

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

        offer = response

        assert "id" in offer, "Offer has no id"

        offer = db.session.query(Offer).filter(Offer.id == offer["id"]).first()
        assert offer, "Offer not found in database"

        assert offer.user_id == user.id, f"User ID does not match {offer.user_id}"
        
        notification_offer_creator = (
            db.session.query(Notification)
            .filter(Notification.user_id == offer.user_id)
            .filter(Notification.question_id == question.id)
            .first()
        )

        # Assert that notification was created
        assert notification_offer_creator, "Notification not created"
        
        # Assert that notification was created for offer_creator
        assert notification_offer_creator.user_id == offer.user_id, "Notification user is not offer_creator"

        notification_question_author = (
            db.session.query(Notification)
            .filter(Notification.user_id == question.user_id)
            .filter(Notification.question_id == question.id)
            .first()
        )

        # Assert that notification was created
        assert notification_question_author, "Notification not created"
        
        # Assert that notification was created for question author
        assert notification_question_author.user_id == question.user_id, "Notification user is not question_author"


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


class TestUpdateOffer:

    def test_update_offer_success(self, client_with_offer, user_jwt):
        """
        Test updating an offer successfully.
        """
        user, jwt = user_jwt

        offer = db.session.query(Offer).first()

        assert offer, "User does not have any offer in Database"
        user = offer.user

        amount = offer.amount

        # Retrieve the original offer as dictionary
        original_offer_dict = offer.to_dict(simplified=False)

        response = client_with_offer.put(
            url_for("backend.offer.update_offer", id_offer=offer.id),
            json={"amount": amount},
            headers=get_jwt_header(user),
        )

        assert response.status_code == HTTPStatus.OK, response.json

        offer = db.session.query(Offer).filter(Offer.id == offer.id).first()

        assert offer.amount == amount, "Offer amount not updated"

        # Retrieve the current offer as dictionary
        offer_dict = offer.to_dict(simplified=False)

        # Assert all attributes are equal except for amount
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if k == "amount" or not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_update_offer_low_price(self, client_with_offer, user_jwt):
        """
        Test updating an offer with an invalid status.
        """
        user, jwt = user_jwt

        offer = db.session.query(Offer).first()

        assert offer, "User does not have any offer in Database"
        user = offer.user

        question = offer.question

        amount = offer.amount

        # Retrieve the original offer as dictionary
        original_offer_dict = offer.to_dict(simplified=False)

        response = client_with_offer.put(
            url_for("backend.offer.update_offer", id_offer=offer.id),
            json={"amount": question.price - 1},
            headers=get_jwt_header(user),
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        # Assert right error message is returned.
        assert response.get_json()["msg"] == "Invalid offer amount", response.get_json()

        # Retrieve the current offer as dictionary
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert all attributes are equal
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_update_offer_unauthorized_user(self, client_with_offer, user_jwt):
        """
        Test updating an offer with an invalid offer ID.
        """
        user, jwt = user_jwt

        offer = db.session.query(Offer).filter(Offer.user_id != user.id).first()

        assert offer, "User does not have any offer in Database"

        question = offer.question

        amount = offer.amount

        # Retrieve the original offer as dictionary
        original_offer_dict = offer.to_dict(simplified=False)

        response = client_with_offer.put(
            url_for("backend.offer.update_offer", id_offer=offer.id),
            json={"amount": question.price},
            headers=jwt,
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json

        assert (
            response.get_json()["msg"]
            == "User is not owner of the offer"
        ), response.json

        # Retrieve the current offer as dictionary
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert all attributes are equal
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"


class TestAcceptOffer:

    def test_accept_offer_success(self, client_with_offer, user_jwt):
        """
        Test accepting an offer successfully.
        """
        user, jwt = user_jwt

        offer = db.session.query(Offer).filter(Offer.active == True).first()

        assert offer, "User does not have any offer in Database"
        user = offer.question.user

        response = client_with_offer.post(
            url_for("backend.offer.accept_offer", offer_id=offer.id),
            headers=get_jwt_header(user),
        )

        assert response.status_code == HTTPStatus.OK, response.json

        offer = db.session.query(Offer).filter(Offer.id == offer.id).first()
        
        original_offer_dict = offer.to_dict(simplified=False)

        assert offer.status == OfferStatusEnum.ACCEPTED, "Offer status not updated"
        assert offer.active == True, "Offer is not active"

        question = offer.question

        other_offers_for_question = (
            db.session.query(Offer)
            .filter(Offer.question_id == question.id)
            .filter(Offer.id != offer.id)
            .all()
        )

        for other_offer in other_offers_for_question:
            assert (
                other_offer.status == OfferStatusEnum.REMOVED
            ), "Other offer status not updated"
            assert other_offer.active == False, "Other offer status not updated"

        notification_offer_creator = (
            db.session.query(Notification)
            .filter(Notification.user_id == offer.user_id)
            .filter(Notification.question_id == question.id)
            .first()
        )

        # Assert that notification was created
        assert notification_offer_creator, "Notification not created"
        
        # Assert that notification was created for offer_creator
        assert notification_offer_creator.user_id == offer.user_id, "Notification user is not offer_creator"

        notification_question_author = (
            db.session.query(Notification)
            .filter(Notification.user_id == question.user_id)
            .filter(Notification.question_id == question.id)
            .first()
        )

        # Assert that notification was created
        assert notification_question_author, "Notification not created"
        
        # Assert that notification was created for question author
        assert notification_question_author.user_id == question.user_id, "Notification user is not question_author"

        # Retrieve the current offer as dictionary
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert all attributes are equal, except active and status
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if (k == "active" or k == "status") and not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_accept_offer_unauthorized_user(self, client_with_offer, user_jwt):
        """
        Test accepting an offer with an invalid offer ID.
        """
        user, jwt = user_jwt

        offer = db.session.query(Offer).filter(Offer.user_id != user.id).first()

        assert offer.question.user != user

        assert offer, "User does not have any offer in Database"

        # Retrieve the original offer as dictionary
        original_offer_dict = offer.to_dict(simplified=False)

        response = client_with_offer.post(
            url_for("backend.offer.accept_offer", offer_id=offer.id),
            headers=jwt,
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json

        assert (
            response.get_json()["msg"] == "User is not author of the question"
        ), response.json

        # Retrieve the current offer as dictionary
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert all attributes are equal
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_offer_status_already_accepted_offer(self, client_with_offer, user_jwt):
        """
        Test accepting an offer with an invalid status.
        """
        user, jwt = user_jwt

        offer = db.session.query(Offer).filter(Offer.active == True).first()

        assert offer, "User does not have any offer in Database"
        user = offer.question.user

        offer.status = OfferStatusEnum.ACCEPTED
        db.session.commit()

        # Retrieve the original offer as dictionary
        original_offer_dict = offer.to_dict(simplified=False)

        response = client_with_offer.post(
            url_for("backend.offer.accept_offer", offer_id=offer.id),
            headers=get_jwt_header(user),
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        # Assert right error message is returned.
        assert (
            response.get_json()["msg"] == "Offer is already accepted"
        ), response.get_json()

        # Retrieve the current offer as dictionary
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert all attributes are equal
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_offer_status_already_declined_offer(self, client_with_offer, user_jwt):
        """
        Test accepting an offer with an invalid status.
        """
        user, jwt = user_jwt

        offer = db.session.query(Offer).filter(Offer.active == True).first()

        assert offer, "User does not have any offer in Database"
        user = offer.question.user

        offer.status = OfferStatusEnum.DECLINED
        offer.active = False
        db.session.commit()

        # Retrieve the original offer as dictionary
        original_offer_dict = offer.to_dict(simplified=False)

        response = client_with_offer.post(
            url_for("backend.offer.accept_offer", offer_id=offer.id),
            headers=get_jwt_header(user),
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        # Assert right error message is returned.
        assert response.get_json()["msg"] == "Offer is not active", response.get_json()

        # Retrieve the current offer as dictionary
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert all attributes are equal
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"


class TestDeclineOffer:

    def test_decline_offer_success(self, client_with_offer, user_jwt):
        """
        Test declining an offer successfully.
        """
        user, jwt = user_jwt

        offer = db.session.query(Offer).filter(Offer.active == True).first()

        assert offer, "User does not have any offer in Database"
        user = offer.question.user

        # Retrieve the original offer as dictionary
        original_offer_dict = offer.to_dict(simplified=False)

        # Make a test API call
        response = client_with_offer.post(
            url_for("backend.offer.decline_offer", offer_id=offer.id),
            headers=get_jwt_header(user),
        )

        # Check response status
        assert response.status_code == HTTPStatus.OK, response.json

        # Check updated fields
        assert offer.status == OfferStatusEnum.DECLINED, "Offer status not updated"
        assert offer.active == False, "Offer still active"

        question = offer.question

        notification_offer_creator = (
            db.session.query(Notification)
            .filter(Notification.user_id == offer.user_id)
            .filter(Notification.question_id == question.id)
            .first()
        )

        # Assert that notification was created
        assert notification_offer_creator, "Notification not created"
        
        # Assert that notification was created for offer_creator
        assert notification_offer_creator.user_id == offer.user_id, "Notification user is not offer_creator"

        notification_question_author = (
            db.session.query(Notification)
            .filter(Notification.user_id == question.user_id)
            .filter(Notification.question_id == question.id)
            .first()
        )

        # Assert that notification was created
        assert notification_question_author, "Notification not created"
        
        # Assert that notification was created for question author
        assert notification_question_author.user_id == question.user_id, "Notification user is not question_author"

        # Retrieve the current offer as dictionary
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert all attributes are equal, except active and status
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if (k == "active" or k == "status") or not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_decline_offer_unauthorized_user(self, client_with_offer, user_jwt):
        """
        Test declining an offer with an invalid offer ID.
        """
        user, jwt = user_jwt

        offer = db.session.query(Offer).filter(Offer.user_id != user.id).first()

        assert offer.question.user != user

        assert offer, "User does not have any offer in Database"

        # Retrieve the original offer as dictionary
        original_offer_dict = offer.to_dict(simplified=False)

        response = client_with_offer.post(
            url_for("backend.offer.decline_offer", offer_id=offer.id),
            headers=jwt,
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json

        assert (
            response.get_json()["msg"] == "User is not author of the question"
        ), response.json

        # Retrieve the current offer as dictionary
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert all attributes are equal
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_decline_offer_invalid_status(self, client_with_offer, user_jwt):
        """
        Test declining an offer with an invalid status.
        """

        user, jwt = user_jwt

        offer = db.session.query(Offer).filter(Offer.active == True).first()

        assert offer, "User does not have any offer in Database"
        user = offer.question.user

        offer.status = OfferStatusEnum.DECLINED
        offer.active = False
        db.session.commit()

        # Retrieve the original offer as dictionary
        original_offer_dict = offer.to_dict(simplified=False)

        response = client_with_offer.post(
            url_for("backend.offer.decline_offer", offer_id=offer.id),
            headers=get_jwt_header(user),
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        # Assert right error message is returned.
        assert response.get_json()["msg"] == "Offer is not active", response.get_json()

        # Retrieve the current offer as dictionary
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert all attributes are equal
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"
