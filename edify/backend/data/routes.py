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
)
from edify import db
from http import HTTPStatus
from edify.utils.utils import internal_request

# -----------------------------------------------------------------------------
# Route Declaration
# -----------------------------------------------------------------------------
# Endpoint: /data/
data = Blueprint("data", __name__, url_prefix="/data")


# -----------------------------------------------------------------------------
# Route Endpoints
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
    subjects = AcademicField.get_list_all(
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
    majors = Major.get_list_all(
        db.session.query(Major).filter_by(school_id=id_school).all()
    )

    return jsonify({"data": majors}), HTTPStatus.OK


# Endpoint: /data/methods
@data.route("/methods", methods=["GET"])
def fetch_methods():
    methods = Method.get_list_all(
        db.session.query(Method).filter_by(supported=True).all()
    )

    return jsonify({"data": methods}), HTTPStatus.OK


# Endpoint: /data/intervals
@data.route("/intervals", methods=["GET"])
def fetch_intervals():
    time_intervals = TimeInterval.get_dict_all(db.session.query(TimeInterval).all())

    return jsonify({"data": time_intervals}), HTTPStatus.OK
