"""Test suite for the Question model and related routes."""

# Standard Library imports
from http import HTTPStatus

# Third-Party Framework imports
from faker import Faker
from flask import url_for

# Local Application imports
from edify.core import db
from edify.models import User, Course, Method, Question
from tests.utils import get_jwt_header, compare_dicts

# Initialize Faker for generating fake data
fake = Faker()


class TestCreateQuestion:
    """Test suite for the Question model and related routes."""

    def test_create_question_success(self, client_with_data, user_jwt):
        """Test creating a question successfully."""
        user, jwt = user_jwt

        method = db.session.query(Method).first()

        course = db.session.query(Course).filter_by(school_id=user.school_id).first()

        solve_time = 30
        price = 10
        request = "What is Python?"

        response = client_with_data.post(
            url_for("backend.question.create_question"),
            data={
                "course_id": course.id,
                "method": method.value,
                "solve_time": solve_time,
                "price": price,
                "request_message": request,
            },
            headers=jwt,
        )
        assert response.status_code == HTTPStatus.CREATED, response.json

        # Get the json representation from the response
        question = response.get_json()

        assert "id" in question, "Question has no id"

        # Find the question in the database
        question = db.session.get(Question, question["id"])
        assert question, "Question not in database"
        assert question.visible, "Question is not visible"

        # Convert to dict
        question = question.to_dict(simplified=False)

        # Assert question was created with the correct attributes
        assert (
            question["user_id"] == user.id
        ), f"User ID does not match {question['user_id']}"

        assert (
            question["request"] == request
        ), f"Request does not match {question['request']}"

        assert (
            question["solve_time_min"] == solve_time
        ), f"Solve time does not match {question['solve_time_min']}"

        assert question["price"] == price, f"Price does not match {question['price']}"

        assert (
            question["method_value"] == method.value
        ), f"Methods do not match {question['method']}"

        assert (
            question["solved"] is False
        ), f"Question should be unsolved {question['solved']}"

        assert (
            question["course_id"] == course.id
        ), f"Course ID does not match {question['course_id']}"

        assert (
            question["course_name"] == course.name
        ), f"Course name does not match {question['course_name']}"

        assert (
            question["course_code"] == course.code
        ), f"Course code does not match {question['class_code']}"

        assert (
            question["academic_field"] == course.academic_field.value
        ), f"Academic field does not match {question['academic_field']}"

    def test_create_question_user_not_found(self, client_with_data, user_jwt):
        """Test creating a question without a user (Unauthorized)."""
        user, _ = user_jwt

        method = db.session.query(Method).first()

        course = db.session.query(Course).filter_by(school_id=user.school_id).first()

        response = client_with_data.post(
            url_for("backend.question.create_question"),
            data={
                "course_id": course.id,
                "method": method.value,
                "solve_time": 30,
                "price": 10.0,
                "request_message": "What is Python?",
            },
            headers=None,
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json

    def test_create_question_invalid_method(self, client_with_data, user_jwt):
        """Test creating a question with an invalid method ID."""
        user, jwt = user_jwt

        invalid_method = "none"  # Assuming this method does not exist

        course = db.session.query(Course).filter_by(school_id=user.school_id).first()

        response = client_with_data.post(
            url_for("backend.question.create_question"),
            data={
                "course_id": course.id,
                "method": invalid_method,
                "solve_time": 30,
                "price": 10.0,
                "request_message": "What is Python?",
            },
            headers=jwt,
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
        assert "Invalid method" in response.get_json()["msg"]


class TestDeleteQuestion:
    """Test suite for deleting a question."""

    def test_delete_question_success(self, client_with_question):
        """Test deleting a question successfully."""
        question = db.session.query(Question).filter(Question.visible.is_(True)).first()

        # Get the user and it's jwt
        user = db.session.get(User, question.user_id)
        jwt = get_jwt_header(user)

        question_id = question.id
        original_question_dict = question.to_dict(simplified=False)

        response = client_with_question.delete(
            url_for("backend.question.delete_question", id_question=question_id),
            headers=jwt,
        )

        assert response.status_code == HTTPStatus.OK, response.json

        # Get the json representation from the response
        question = response.get_json()

        assert "id" in question, "Question has no id"

        # Find the question in the database
        question = db.session.get(Question, question["id"])
        assert question, "Question not in database"
        assert question.visible is False, "Question is visible and was not removed"

        # Convert to dict
        question_dict = question.to_dict(simplified=False)

        # Assert all attributes are equal except for visibility
        compare_dicts(original_question_dict, question_dict, keys_to_skip=["visible"])

    def test_delete_question_unauthorized_user(self, client_with_question, user_jwt):
        """Test deleting a question by a user who is not the owner of the question."""
        user, jwt = user_jwt

        # Query for a question not owned by the user
        question = (
            db.session.query(Question).filter(Question.user_id != user.id).first()
        )

        # Assert that such a question exists in the database
        assert question, "User does not have any question in Database"

        # Retrieve the original question as a dictionary
        original_question_dict = question.to_dict(simplified=False)

        # Send request to delete the question with an unauthorized user
        response = client_with_question.delete(
            url_for("backend.question.delete_question", id_question=question.id),
            headers=jwt,
        )

        # Assert that the response status code is 401 (Unauthorized)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json

        # Assert that the correct error message is returned
        assert (
            response.get_json()["msg"] == "User is not the author of the question"
        ), response.json

        # Retrieve the current question as a dictionary
        question_dict = db.session.get(Question, question.id).to_dict(simplified=False)

        # Assert all attributes are equal (no changes should have been made)
        compare_dicts(original_question_dict, question_dict)

    def test_delete_question_not_visible(self, client_with_question):
        """Test deleting a question that is not visible."""
        question = db.session.query(Question).first()

        # Assert that such a question exists in the database
        assert question, "No questions in Database"

        # Get the user and it's jwt
        user = db.session.get(User, question.user_id)
        jwt = get_jwt_header(user)

        question.visible = False
        db.session.commit()

        # Retrieve the original question as a dictionary
        original_question_dict = question.to_dict(simplified=False)

        # Send request to delete the question with an unauthorized user
        response = client_with_question.delete(
            url_for("backend.question.delete_question", id_question=question.id),
            headers=jwt,
        )

        # Assert that the response status code is 401 (Unauthorized)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json

        # Assert that the correct error message is returned
        assert response.get_json()["msg"] == "Question is hidden", response.json

        # Retrieve the current question as a dictionary
        question_dict = db.session.get(Question, question.id).to_dict(simplified=False)

        # Assert all attributes are equal (no changes should have been made)
        compare_dicts(original_question_dict, question_dict)

    def test_delete_question_not_found(self, client_with_question, user_jwt):
        """Test deleting a question that does not exist."""
        _, jwt = user_jwt

        # Send request to delete the question with a random id
        response = client_with_question.delete(
            url_for("backend.question.delete_question", id_question=999),
            headers=jwt,
        )

        assert response.status_code == HTTPStatus.NOT_FOUND, response.json
        assert response.get_json()["msg"] == "Question not found", response.json
