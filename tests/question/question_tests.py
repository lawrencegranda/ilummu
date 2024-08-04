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
from edify.models import User, AcademicField, Course, Method, Question

# Initialize Faker for generating fake data
fake = Faker()


@pytest.fixture
def setup_data(client_with_db, jwt_headers):
    """
    A fixture to set up necessary data for tests.
    """
    method = Method(value="chat", name="Chat")
    academic_field = AcademicField(value="CS", name="Computer Science", school_id=1)
    course = Course(
        code="CS101", name="Introduction to CS", academic_field_id=1, school_id=1
    )
    db.session.add_all([method, academic_field, course])
    db.session.commit()
    return {
        "method_id": method.id,
        "academic_field": academic_field.value,
        "class_code": course.code,
        "class_name": course.name,
    }


class TestCreateQuestion:

    def test_create_question_success(self, client_with_db, jwt_headers, setup_data):
        """
        Test creating a question successfully.
        """
        response = client_with_db.post(
            url_for("backend.question.create_question"),
            json={
                "class_code": setup_data["class_code"],
                "class_name": setup_data["class_name"],
                "academic_field": setup_data["academic_field"],
                "method_id": setup_data["method_id"],
                "solve_time": 30,
                "price": 10.0,
                "request_message": "What is Python?",
            },
            headers=jwt_headers,
        )
        assert response.status_code == HTTPStatus.CREATED, response.json
        assert "id" in response.get_json()

    def test_create_question_user_not_found(self, client_with_db, setup_data):
        """
        Test creating a question without a user (Unauthorized).
        """
        response = client_with_db.post(
            url_for("backend.question.create_question"),
            json={
                "class_code": setup_data["class_code"],
                "class_name": setup_data["class_name"],
                "academic_field": setup_data["academic_field"],
                "method_id": setup_data["method_id"],
                "solve_time": 30,
                "price": 10.0,
                "request_message": "What is Python?",
            },
            headers=None,
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED, response.json

    def test_create_question_invalid_method(
        self, client_with_db, jwt_headers, setup_data
    ):
        """
        Test creating a question with an invalid method ID.
        """
        invalid_method_id = 999  # Assuming this method does not exist
        response = client_with_db.post(
            url_for("backend.question.create_question"),
            json={
                "class_code": setup_data["class_code"],
                "class_name": setup_data["class_name"],
                "academic_field": setup_data["academic_field"],
                "method_id": invalid_method_id,
                "solve_time": 30,
                "price": 10.0,
                "request_message": "What is Python?",
            },
            headers=jwt_headers,
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
        assert response.get_json()["error"] == "Invalid method ID"

    def test_create_question_invalid_academic_field(
        self, client_with_db, jwt_headers, setup_data
    ):
        """
        Test creating a question with an invalid academic field.
        """
        response = client_with_db.post(
            url_for("backend.question.create_question"),
            json={
                "class_code": setup_data["class_code"],
                "class_name": setup_data["class_name"],
                "academic_field": "InvalidField",  # Invalid academic field
                "method_id": setup_data["method_id"],
                "solve_time": 30,
                "price": 10.0,
                "request_message": "What is Python?",
            },
            headers=jwt_headers,
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
