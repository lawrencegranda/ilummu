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
from tests.utils import get_jwt_header

# Initialize Faker for generating fake data
fake = Faker()


class TestCreateQuestion:

    def test_create_question_success(self, client_with_data, user_jwt):
        """
        Test creating a question successfully.
        """
        user, jwt = user_jwt

        method = db.session.query(Method).first()

        course = db.session.query(Course).filter_by(school_id=user.school_id).first()
        course_name = course.name
        course_code = course.code

        academic_field = course.academic_field

        solve_time = 30
        price = 10
        request = "What is Python?"

        response = client_with_data.post(
            url_for("backend.question.create_question"),
            json={
                "class_code": course_code,
                "class_name": course_name,
                "academic_field": academic_field.value,
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
        assert question.visible == True, "Question is not visible"

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
            question["solved"] == False
        ), f"Question should be unsolved {question['solved']}"

        assert (
            question["course_id"] == course.id
        ), f"Course ID does not match {question['course_id']}"

        assert (
            question["course_name"] == course_name
        ), f"Course name does not match {question['course_name']}"

        assert (
            question["course_code"] == course_code
        ), f"Course code does not match {question['class_code']}"

        assert (
            question["academic_field"] == academic_field.value
        ), f"Academic field does not match {question['academic_field']}"

    def test_create_question_success_new_course(self, client_with_data, user_jwt):
        """
        Test creating a question successfully, but with a new course (needs to creae
        one in the endpoint).
        """
        user, jwt = user_jwt

        method = db.session.query(Method).first()

        course_name = "New Course"
        course_code = "000101"

        academic_field = (
            db.session.query(AcademicField).filter_by(school_id=user.school_id).first()
        )

        solve_time = 30
        price = 10
        request = "What is Python?"

        response = client_with_data.post(
            url_for("backend.question.create_question"),
            json={
                "class_code": course_code,
                "class_name": course_name,
                "academic_field": academic_field.value,
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
        assert question.visible == True, "Question is not visible"

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
            question["solved"] == False
        ), f"Question should be unsolved {question['solved']}"

        assert (
            question["course_name"] == course_name
        ), f"Course name does not match {question['course_name']}"

        assert (
            question["course_code"] == course_code
        ), f"Course code does not match {question['class_code']}"

        assert (
            question["academic_field"] == academic_field.value
        ), f"Academic field does not match {question['academic_field']}"

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


class TestDeleteQuestion:

    def test_delete_question_success(self, client_with_question):
        """
        Test deleting a question successfully.
        """
        question = db.session.query(Question).filter(Question.visible == True).first()

        # Get the user and it's jwt
        user = db.session.get(User, question.user_id)
        jwt = get_jwt_header(user)

        question_id = question.id
        original_question_dict = question.to_dict(simplified=False)

        response = client_with_question.delete(
            url_for("backend.question.delete_question", question_id=question_id),
            headers=jwt,
        )

        assert response.status_code == HTTPStatus.OK, response.json

        # Get the json representation from the response
        question = response.get_json()

        assert "id" in question, "Question has no id"

        # Find the question in the database
        question = db.session.get(Question, question["id"])
        assert question, "Question not in database"
        assert question.visible == False, "Question is visible and was not removed"

        # Convert to dict
        question_dict = question.to_dict(simplified=False)

        # Assert all attributes are equal except for visibility
        for (k, v1), (k2, v2) in zip(
            original_question_dict.items(), question_dict.items()
        ):
            assert k == k2, f"Keys are not equal ({k} != {k2})"

            if k == "visible":
                continue

            assert v1 == v1, f"Values for {k} are not equal ({v1} != {v2})"
