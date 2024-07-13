from flask import Blueprint, url_for, jsonify, current_app, redirect
from flask_jwt_extended import jwt_required, current_user
from edify.backend.user.routes import get_current_user
from edify.models import (
    User,
    Notification,
    AcademicField,
    Method,
    TimeInterval,
    Course,
    School,
    NotificationType,
    Major,
    Question,
    Notification,
    Offer,
)
from edify import db
from http import HTTPStatus
from edify.utils.utils import internal_request, error_response
from edify.utils.constants import ErrorType
from edify.utils.decorators import author_required

# -----------------------------------------------------------------------------
# Route Blueprint
# -----------------------------------------------------------------------------
# Endpoint: /data/
data = Blueprint("data", __name__, url_prefix="/data")


# -----------------------------------------------------------------------------
# Blueprint Endpoints (data)
# -----------------------------------------------------------------------------


# Endpoint: /data/subjects
@data.route("/subjects", methods=["GET"])
@jwt_required(optional=True)
def fetch_user_subjects():
    user = get_current_user()

    if user:
        school = user.school
    else:
        school = db.session.query(School).filter_by(name="Cornell University").first()

    response, status = internal_request(
        url_for("backend.data.fetch_school_subjects", id_school=school.id), method="GET"
    )

    return jsonify(response), status


# Endpoint: /data/school/<id_school>/subjects
@data.route("/school/<int:id_school>/subjects", methods=["GET"])
def fetch_school_subjects(id_school):
    subjects = AcademicField.to_dict_all(
        db.session.query(AcademicField).filter_by(school_id=id_school).all()
    )

    return jsonify({"data": subjects}), HTTPStatus.OK


# Endpoint: /data/majors
@data.route("/majors", methods=["GET"])
@jwt_required(optional=True)
def fetch_user_majors():
    user = get_current_user()

    if user:
        school = user.school
    else:
        school = db.session.query(School).filter_by(name="Cornell University").first()

    response, status = internal_request(
        url_for("backend.data.fetch_school_majors", id_school=school.id), method="GET"
    )

    return jsonify(response), status


# Endpoint: /data/school/<id_school>/majors
@data.route("/school/<int:id_school>/majors", methods=["GET"])
def fetch_school_majors(id_school):
    majors = Major.to_dict_all(
        db.session.query(Major).filter_by(school_id=id_school).all()
    )

    return jsonify({"data": majors}), HTTPStatus.OK


# Endpoint: /data/methods
@data.route("/methods", methods=["GET"])
def fetch_methods():
    methods = Method.to_dict_all(
        db.session.query(Method).filter_by(supported=True).all()
    )

    return jsonify({"data": methods}), HTTPStatus.OK


# Endpoint: /data/intervals
@data.route("/intervals", methods=["GET"])
def fetch_intervals():
    time_intervals = TimeInterval.to_dict_all(db.session.query(TimeInterval).all())

    return jsonify({"data": time_intervals}), HTTPStatus.OK


# Endpoint: /data/notifications
@data.route("/notifications", methods=["GET"])
def fetch_user_notifications():
    user = get_current_user()

    if not user:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    notifications = []
    if user:
        notifications = Notification.to_dict_all(user.notifications)

    return jsonify({"data": notifications}), HTTPStatus.OK


# Endpoint: /data/questions
@data.route("/questions", methods=["GET"])
def fetch_questions():
    questions = Question.to_dict_all(db.session.query(Question).all())

    return jsonify({"data": questions}), HTTPStatus.OK


# Endpoint: /data/question/<id_question>
@data.route("/question/<int:id_question>", methods=["GET"])
@jwt_required(optional=True)
def get_question(id_question):
    question = db.session.query(Question).get(id_question)

    if not question:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    qstn_dict = Question.to_dict_all([question])[0]

    return jsonify({"data": [qstn_dict]}), HTTPStatus.OK


# Endpoint: /data/question/<id_question>/is_author
@data.route("/question/<int:id_question>/is_author", methods=["GET"])
@jwt_required()
def is_question_author(id_question):
    question = db.session.query(Question).get(id_question)
    if not question:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    user = get_current_user()
    if not user:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    is_author = question.user_id == user.id

    return jsonify({"data": [is_author]}), HTTPStatus.OK


# Endpoint: /data/question/<id_question>/offer_made
@data.route("/question/<int:id_question>/offer_made", methods=["GET"])
@jwt_required()
def question_offer_made(id_question):
    question = db.session.query(Question).get(id_question)
    if not question:
        return error_response("Question not found", ErrorType.NOT_FOUND)

    user = get_current_user()
    if not user:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    offer_made = (
        db.session.query(Offer)
        .filter_by(question_id=question.id, user_id=user.id, active=True)
        .first()
    )

    if not offer_made:
        return jsonify({"data": []}), HTTPStatus.OK

    return jsonify({"data": [offer_made.to_dict(simplified=False)]}), HTTPStatus.OK


# Endpoint: /data/question/<id_question>/offers_received
@data.route("/question/<int:id_question>/offers_received", methods=["GET"])
@jwt_required()
@author_required("id_question")
def offers_received(id_question):
    question = db.session.query(Question).get(id_question)
    user = get_current_user()

    offers = (
        db.session.query(Offer).filter_by(question_id=question.id, active=True).all()
    )

    offers = Offer.to_dict_all(offers)

    return jsonify({"data": offers}), HTTPStatus.OK
