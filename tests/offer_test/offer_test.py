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

        # Query for a question not created by the current user, that is visible and unsolved
        question = (
            db.session.query(Question)
            .filter(Question.user_id != user.id)
            .filter(Question.visible == True)
            .filter(Question.solved == False)
            .first()
        )

        question_id = question.id
        price = 1.5 * question.price  # Set offer price as 1.5 times the question price

        # Send a POST request to create an offer
        response = client_with_question.post(
            url_for("backend.offer.create_offer"),
            json={"question_id": question_id, "price": price},
            headers=jwt,
        )

        # Assert that the response status code is 201 (Created)
        assert response.status_code == HTTPStatus.CREATED, response.json

        response = response.get_json()
        offer = response

        # Assert that the created offer has an ID
        assert "id" in offer, "Offer has no id"

        # Query the database to check if the offer exists
        offer = db.session.query(Offer).filter(Offer.id == offer["id"]).first()
        assert offer, "Offer not found in database"

        # Assert that the offer user ID matches the current user ID
        assert offer.user_id == user.id, f"User ID does not match {offer.user_id}"
        
        # Query for a notification created for the offer creator
        notification_offer_creator = (
            db.session.query(Notification)
            .filter(Notification.user_id == offer.user_id)
            .filter(Notification.question_id == question.id)
            .first()
        )

        # Assert that notification was created for the offer creator
        assert notification_offer_creator, "Notification not created"
        assert notification_offer_creator.user_id == offer.user_id, "Notification user is not offer_creator"

        # Query for a notification created for the question author
        notification_question_author = (
            db.session.query(Notification)
            .filter(Notification.user_id == question.user_id)
            .filter(Notification.question_id == question.id)
            .first()
        )

        # Assert that notification was created for the question author
        assert notification_question_author, "Notification not created"
        assert notification_question_author.user_id == question.user_id, "Notification user is not question_author"

    def test_create_offer_invalid_question(self, client_with_question, user_jwt):
        """
        Test creating an offer with an invalid question ID.
        """
        user, jwt = user_jwt

        # Send a POST request with an invalid question ID
        response = client_with_question.post(
            url_for("backend.offer.create_offer"),
            json={"question_id": -1, "price": 10},
            headers=jwt,
        )

        # Assert that the response status code is 404 (Not Found)
        assert response.status_code == HTTPStatus.NOT_FOUND, response.json

        # Assert that the response message indicates the question does not exist
        assert response.get_json()["msg"] == "Question does not exist"
        

    def test_create_offer_existing_offer(self, client_with_question, user_jwt):
        """
        Test creating an offer when the user has already made an offer.
        """
        user, jwt = user_jwt

        # Query for a question not created by the current user, that is visible and unsolved
        question = (
            db.session.query(Question)
            .filter(Question.user_id != user.id)
            .filter(Question.visible == True)
            .filter(Question.solved == False)
            .first()
        )

        question_id = question.id
        price = 1.5 * question.price

        # Create an offer for the selected question
        offer = Offer(
            user_id=user.id,
            question_id=question_id,
            amount=price,
        )

        # Add the offer to the session and commit it
        db.session.add(offer)
        db.session.commit()

        # Send a POST request to create another offer for the same question
        response = client_with_question.post(
            url_for("backend.offer.create_offer"),
            json={"question_id": question_id, "price": price},
            headers=jwt,
        )

        # Assert that the response status code is 400 (Bad Request)
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        # Assert that the response message indicates the user already made an offer
        assert response.get_json()["msg"] == "User already made offer to question"

    def test_create_offer_not_visible_question(self, client_with_question, user_jwt):
        """
        Test creating an offer when the question is not visible.
        """
        user, jwt = user_jwt

        # Query for a question not created by the current user, that is visible and unsolved
        question = (
            db.session.query(Question)
            .filter(Question.user_id != user.id)
            .filter(Question.visible == True)
            .filter(Question.solved == False)
            .first()
        )

        # Mark the question as not visible
        question.visible = False
        db.session.commit()

        assert question, "User cannot create Offer for any question in database"

        question_id = question.id
        price = 1.5 * question.price

        # Send a POST request to create an offer for a non-visible question
        response = client_with_question.post(
            url_for("backend.offer.create_offer"),
            json={"question_id": question_id, "price": price},
            headers=jwt,
        )

        # Assert that the response status code is 400 (Bad Request)
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        # Assert that the response message indicates the question is not visible
        assert response.get_json()["msg"] == "Question is not visible"

    def test_create_offer_solved_question(self, client_with_question, user_jwt):
        """
        Test creating an offer when the question is already solved.
        """
        user, jwt = user_jwt

        # Query for a question not created by the current user, that is visible and unsolved
        question = (
            db.session.query(Question)
            .filter(Question.user_id != user.id)
            .filter(Question.solved == False)
            .filter(Question.visible == True)
            .first()
        )

        # Mark the question as solved
        question.solved = True
        db.session.commit()

        assert question, "User cannot create Offer for any question in Database"

        question_id = question.id
        price = 1.5 * question.price

        # Send a POST request to create an offer for a solved question
        response = client_with_question.post(
            url_for("backend.offer.create_offer"),
            json={"question_id": question_id, "price": price},
            headers=jwt,
        )

        # Assert that the response status code is 400 (Bad Request)
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        # Assert that the response message indicates the question is already solved
        assert response.get_json()["msg"] == "Question is already solved"

class TestGetOffer:

    def test_get_offer_success(self, client_with_offer, user_jwt):
        """
        Test getting an offer successfully.
        """
        user, jwt = user_jwt

        # Query for the first offer in the database
        offer = db.session.query(Offer).first()

        # Assert that an offer exists in the database
        assert offer, "User does not have any offer in Database"

        # Send a GET request to retrieve the offer
        response = client_with_offer.get(
            url_for("backend.offer.get_offer", id_offer=offer.id), headers=jwt
        )

        # Assert that the response status code is 200 (OK)
        assert response.status_code == HTTPStatus.OK, response.json

        # Parse the JSON response
        offer = response.get_json()

        # Assert that the offer was found in the response
        assert offer, "Offer not found in database"

    def test_get_offer_invalid_id_offer(self, client_with_offer, user_jwt):
        """
        Test getting an offer with an invalid offer ID.
        """
        user, jwt = user_jwt

        # Send a GET request with an invalid offer ID
        response = client_with_offer.get(
            url_for("backend.offer.get_offer", id_offer=0), headers=jwt
        )

        # Assert that the response status code is 404 (Not Found)
        assert response.status_code == HTTPStatus.NOT_FOUND, response.json

        # Assert that the response message indicates the offer was not found
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

        # Query for the first offer in the database
        offer = db.session.query(Offer).first()

        # Assert that an offer exists in the database
        assert offer, "User does not have any offer in Database"
        user = offer.user

        amount = offer.amount

        # Retrieve the original offer as a dictionary
        original_offer_dict = offer.to_dict(simplified=False)

        # Send a PUT request to update the offer amount
        response = client_with_offer.put(
            url_for("backend.offer.update_offer", id_offer=offer.id),
            json={"amount": amount},
            headers=get_jwt_header(user),
        )

        # Assert that the response status code is 200 (OK)
        assert response.status_code == HTTPStatus.OK, response.json

        # Query the updated offer from the database
        offer = db.session.query(Offer).filter(Offer.id == offer.id).first()

        # Assert that the offer amount was updated successfully
        assert offer.amount == amount, "Offer amount not updated"

        # Retrieve the current offer as a dictionary
        offer_dict = offer.to_dict(simplified=False)

        # Assert all attributes are equal except for the amount
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            # Skip checking for amount and non-primitive types
            if k == "amount" or not isinstance(v1, primitives):
                continue

            # Assert that all other values remain unchanged
            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_update_offer_low_price(self, client_with_offer, user_jwt):
        """
        Test updating an offer with a price lower than the question price.
        """
        user, jwt = user_jwt

        # Query for the first offer in the database
        offer = db.session.query(Offer).first()

        # Assert that an offer exists in the database
        assert offer, "User does not have any offer in Database"
        user = offer.user

        question = offer.question
        amount = offer.amount

        # Retrieve the original offer as a dictionary
        original_offer_dict = offer.to_dict(simplified=False)

        # Send a PUT request with an invalid (lower) offer amount
        response = client_with_offer.put(
            url_for("backend.offer.update_offer", id_offer=offer.id),
            json={"amount": question.price - 1},
            headers=get_jwt_header(user),
        )

        # Assert that the response status code is 400 (Bad Request)
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        # Assert that the correct error message is returned
        assert response.get_json()["msg"] == "Invalid offer amount", response.get_json()

        # Retrieve the current offer as a dictionary
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert all attributes are equal (no changes should have been made)
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            # Skip non-primitive types
            if not isinstance(v1, primitives):
                continue

            # Assert that all values remain unchanged
            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_update_offer_unauthorized_user(self, client_with_offer, user_jwt):
        """
        Test updating an offer by a user who is not the owner of the offer.
        """
        user, jwt = user_jwt

        # Query for an offer not owned by the user
        offer = db.session.query(Offer).filter(Offer.user_id != user.id).first()

        # Assert that such an offer exists in the database
        assert offer, "User does not have any offer in Database"

        question = offer.question
        amount = offer.amount

        # Retrieve the original offer as a dictionary
        original_offer_dict = offer.to_dict(simplified=False)

        # Send a PUT request to update the offer amount with an unauthorized user
        response = client_with_offer.put(
            url_for("backend.offer.update_offer", id_offer=offer.id),
            json={"amount": question.price},
            headers=jwt,
        )

        # Assert that the response status code is 401 (Unauthorized)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json

        # Assert that the correct error message is returned
        assert (
            response.get_json()["msg"]
            == "User is not owner of the offer"
        ), response.json

        # Retrieve the current offer as a dictionary
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert all attributes are equal (no changes should have been made)
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            # Skip non-primitive types
            if not isinstance(v1, primitives):
                continue

            # Assert that all values remain unchanged
            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"
            
            
class TestAcceptOffer:

    def test_accept_offer_success(self, client_with_offer, user_jwt):
        """
        Test accepting an offer successfully.
        """
        # Extract user and JWT from the provided user_jwt fixture.
        user, jwt = user_jwt

        # Query the first active offer from the database.
        offer = db.session.query(Offer).filter(Offer.active == True).first()

        # Assert that the offer exists in the database.
        assert offer, "User does not have any offer in Database"

        # Set the user to be the question's author associated with the offer.
        user = offer.question.user

        # Make a POST request to accept the offer.
        response = client_with_offer.post(
            url_for("backend.offer.accept_offer", offer_id=offer.id),
            headers=get_jwt_header(user),
        )

        # Assert that the response status code is 200 OK.
        assert response.status_code == HTTPStatus.OK, response.json

        # Reload the offer to check for changes after the request.
        offer = db.session.query(Offer).filter(Offer.id == offer.id).first()
        original_offer_dict = offer.to_dict(simplified=False)

        # Assert that the offer status is updated to ACCEPTED and is still active.
        assert offer.status == OfferStatusEnum.ACCEPTED, "Offer status not updated"
        assert offer.active == True, "Offer is not active"

        # Get the question associated with the offer.
        question = offer.question

        # Fetch all other offers related to the same question, excluding the accepted one.
        other_offers_for_question = (
            db.session.query(Offer)
            .filter(Offer.question_id == question.id)
            .filter(Offer.id != offer.id)
            .all()
        )

        # Assert that the statuses of all other offers are updated to REMOVED and inactive.
        for other_offer in other_offers_for_question:
            assert (
                other_offer.status == OfferStatusEnum.REMOVED
            ), "Other offer status not updated"
            assert other_offer.active == False, "Other offer status not updated"

        # Check if a notification was created for the offer creator.
        notification_offer_creator = (
            db.session.query(Notification)
            .filter(Notification.user_id == offer.user_id)
            .filter(Notification.question_id == question.id)
            .first()
        )

        # Assert that a notification was created and it is associated with the offer creator.
        assert notification_offer_creator, "Notification not created"
        assert notification_offer_creator.user_id == offer.user_id, "Notification user is not offer_creator"

        # Check if a notification was created for the question's author.
        notification_question_author = (
            db.session.query(Notification)
            .filter(Notification.user_id == question.user_id)
            .filter(Notification.question_id == question.id)
            .first()
        )

        # Assert that a notification was created and it is associated with the question author.
        assert notification_question_author, "Notification not created"
        assert notification_question_author.user_id == question.user_id, "Notification user is not question_author"

        # Reload the current offer's details and convert them to a dictionary.
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Compare all attributes of the original and current offer dictionaries, except 'active' and 'status'.
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if (k == "active" or k == "status") and not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_accept_offer_unauthorized_user(self, client_with_offer, user_jwt):
        """
        Test accepting an offer with an invalid offer ID.
        """
        # Extract user and JWT from the provided user_jwt fixture.
        user, jwt = user_jwt

        # Query the first offer not owned by the user.
        offer = db.session.query(Offer).filter(Offer.user_id != user.id).first()

        # Assert that the queried offer is not associated with the user.
        assert offer.question.user != user

        # Assert that the offer exists in the database.
        assert offer, "User does not have any offer in Database"

        # Retrieve the original offer details as a dictionary.
        original_offer_dict = offer.to_dict(simplified=False)

        # Make a POST request to accept the offer with unauthorized credentials.
        response = client_with_offer.post(
            url_for("backend.offer.accept_offer", offer_id=offer.id),
            headers=jwt,
        )

        # Assert that the response status code is 401 UNAUTHORIZED.
        assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json

        # Assert that the error message returned is correct.
        assert (
            response.get_json()["msg"] == "User is not author of the question"
        ), response.json

        # Reload the current offer's details and convert them to a dictionary.
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert that all attributes of the original and current offer dictionaries are equal.
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_offer_status_already_accepted_offer(self, client_with_offer, user_jwt):
        """
        Test accepting an offer with an invalid status.
        """
        # Extract user and JWT from the provided user_jwt fixture.
        user, jwt = user_jwt

        # Query the first active offer from the database.
        offer = db.session.query(Offer).filter(Offer.active == True).first()

        # Assert that the offer exists in the database.
        assert offer, "User does not have any offer in Database"

        # Set the user to be the question's author associated with the offer.
        user = offer.question.user

        # Set the offer status to ACCEPTED to simulate an already accepted offer.
        offer.status = OfferStatusEnum.ACCEPTED
        db.session.commit()

        # Retrieve the original offer details as a dictionary.
        original_offer_dict = offer.to_dict(simplified=False)

        # Make a POST request to accept the already accepted offer.
        response = client_with_offer.post(
            url_for("backend.offer.accept_offer", offer_id=offer.id),
            headers=get_jwt_header(user),
        )

        # Assert that the response status code is 400 BAD REQUEST.
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        # Assert that the error message returned is correct.
        assert (
            response.get_json()["msg"] == "Offer is already accepted"
        ), response.get_json()

        # Reload the current offer's details and convert them to a dictionary.
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert that all attributes of the original and current offer dictionaries are equal.
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_offer_status_already_declined_offer(self, client_with_offer, user_jwt):
        """
        Test accepting an offer with an invalid status.
        """
        # Extract user and JWT from the provided user_jwt fixture.
        user, jwt = user_jwt

        # Query the first active offer from the database.
        offer = db.session.query(Offer).filter(Offer.active == True).first()

        # Assert that the offer exists in the database.
        assert offer, "User does not have any offer in Database"

        # Set the user to be the question's author associated with the offer.
        user = offer.question.user

        # Set the offer status to DECLINED and inactive to simulate an already declined offer.
        offer.status = OfferStatusEnum.DECLINED
        offer.active = False
        db.session.commit()

        # Retrieve the original offer details as a dictionary.
        original_offer_dict = offer.to_dict(simplified=False)

        # Make a POST request to accept the already declined offer.
        response = client_with_offer.post(
            url_for("backend.offer.accept_offer", offer_id=offer.id),
            headers=get_jwt_header(user),
        )

        # Assert that the response status code is 400 BAD REQUEST.
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        # Assert that the error message returned is correct.
        assert response.get_json()["msg"] == "Offer is not active", response.get_json()

        # Reload the current offer's details and convert them to a dictionary.
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Assert that all attributes of the original and current offer dictionaries are equal.
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            # Skip comparison for complex types
            if not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

class TestDeclineOffer:

    def test_decline_offer_success(self, client_with_offer, user_jwt):
        """
        Test declining an offer successfully.
        """
        user, jwt = user_jwt

        # Fetch an active offer from the database
        offer = db.session.query(Offer).filter(Offer.active == True).first()

        # Verify that there is an offer in the database
        assert offer, "User does not have any offer in Database"
        
        # Ensure that the user is the author of the question
        user = offer.question.user

        # Retrieve the original offer as a dictionary for comparison
        original_offer_dict = offer.to_dict(simplified=False)

        # Make a test API call to decline the offer
        response = client_with_offer.post(
            url_for("backend.offer.decline_offer", offer_id=offer.id),
            headers=get_jwt_header(user),
        )

        # Check if the response status is OK (200)
        assert response.status_code == HTTPStatus.OK, response.json

        # Check if the offer status is correctly updated to 'DECLINED'
        assert offer.status == OfferStatusEnum.DECLINED, "Offer status not updated"
        assert offer.active == False, "Offer still active"

        # Fetch the related question
        question = offer.question

        # Check for the creation of a notification for the offer creator
        notification_offer_creator = (
            db.session.query(Notification)
            .filter(Notification.user_id == offer.user_id)
            .filter(Notification.question_id == question.id)
            .first()
        )

        # Assert that a notification was created for the offer creator
        assert notification_offer_creator, "Notification not created"
        assert notification_offer_creator.user_id == offer.user_id, "Notification user is not offer_creator"

        # Check for the creation of a notification for the question author
        notification_question_author = (
            db.session.query(Notification)
            .filter(Notification.user_id == question.user_id)
            .filter(Notification.question_id == question.id)
            .first()
        )

        # Assert that a notification was created for the question author
        assert notification_question_author, "Notification not created"
        assert notification_question_author.user_id == question.user_id, "Notification user is not question_author"

        # Retrieve the current offer as a dictionary for comparison
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Ensure that all attributes are equal except 'active' and 'status'
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            # Skip comparison for 'active' and 'status' or any complex types
            if (k == "active" or k == "status") or not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_decline_offer_unauthorized_user(self, client_with_offer, user_jwt):
        """
        Test declining an offer with an unauthorized user.
        """
        user, jwt = user_jwt

        # Fetch an offer not associated with the current user
        offer = db.session.query(Offer).filter(Offer.user_id != user.id).first()

        # Ensure the offer is not authored by the current user
        assert offer.question.user != user

        # Verify that there is an offer in the database
        assert offer, "User does not have any offer in Database"

        # Retrieve the original offer as a dictionary for comparison
        original_offer_dict = offer.to_dict(simplified=False)

        # Attempt to decline the offer with an unauthorized user
        response = client_with_offer.post(
            url_for("backend.offer.decline_offer", offer_id=offer.id),
            headers=jwt,
        )

        # Check if the response status is UNAUTHORIZED (401)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json

        # Verify the correct error message is returned
        assert (
            response.get_json()["msg"] == "User is not author of the question"
        ), response.json

        # Retrieve the current offer as a dictionary for comparison
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Ensure all attributes remain unchanged
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            # Skip comparison for complex types
            if not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"

    def test_decline_offer_invalid_status(self, client_with_offer, user_jwt):
        """
        Test declining an offer that has already been declined.
        """

        user, jwt = user_jwt

        # Fetch an active offer from the database
        offer = db.session.query(Offer).filter(Offer.active == True).first()

        # Verify that there is an offer in the database
        assert offer, "User does not have any offer in Database"
        
        # Ensure the user is the author of the question
        user = offer.question.user

        # Manually set the offer status to 'DECLINED' and deactivate it
        offer.status = OfferStatusEnum.DECLINED
        offer.active = False
        db.session.commit()

        # Retrieve the original offer as a dictionary for comparison
        original_offer_dict = offer.to_dict(simplified=False)

        # Attempt to decline the offer that is already declined
        response = client_with_offer.post(
            url_for("backend.offer.decline_offer", offer_id=offer.id),
            headers=get_jwt_header(user),
        )

        # Check if the response status is BAD_REQUEST (400)
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json

        # Verify the correct error message is returned
        assert response.get_json()["msg"] == "Offer is not active", response.get_json()

        # Retrieve the current offer as a dictionary for comparison
        offer_dict = db.session.get(Offer, offer.id).to_dict(simplified=False)

        # Ensure all attributes remain unchanged
        for (k, v1), (k2, v2) in zip(original_offer_dict.items(), offer_dict.items()):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            # Skip comparison for complex types
            if not isinstance(v1, primitives):
                continue

            assert v1 == v2, f"Values for '{k}' are not equal ({v1} != {v2})"