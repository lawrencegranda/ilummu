"""Data-related endpoints for fetching courses, subjects, and other reference data."""

# Standard Library imports

# Third-Party Framework imports
from flask import Blueprint, url_for
from flask.typing import ResponseReturnValue
from flask_jwt_extended import jwt_required

# Local Application imports
from edify.core import db
from edify.backend.user.utils import get_current_user
from edify.models import (
    AcademicField,
    Course,
    Major,
    Method,
    Notification,
    School,
    TimeInterval,
)
from edify.utils.constants import ErrorType
from edify.utils.utils import error_response, internal_request, data_response


# -----------------------------------------------------------------------------
# Route Blueprint
# -----------------------------------------------------------------------------
# Endpoint: /backend/data/
data = Blueprint("data", __name__, url_prefix="/data")


# -----------------------------------------------------------------------------
# Blueprint Endpoints (data)
# -----------------------------------------------------------------------------


# Endpoint: /backend/data/courses
@data.route("/courses", methods=["GET"])
@jwt_required(optional=True)
def fetch_user_courses() -> ResponseReturnValue:
    """
    Fetch the courses associated with the current user if authenticated,
    otherwise fetch courses for 'Cornell University'.

    Returns:
        JSON response with the courses.
    """
    user = get_current_user()
    if user:
        # If user is logged in, get their school
        school = user.school
    else:
        # If no user is logged in, default to Cornell University
        school = db.session.query(School).filter_by(name="Cornell University").first()

    # Call another endpoint to fetch courses for the school
    response = internal_request(
        url_for("backend.data.fetch_school_courses", id_school=school.id), method="GET"
    )
    return response


# Endpoint: /backend/data/school/<id_school>/courses
@data.route("/school/<int:id_school>/courses", methods=["GET"])
def fetch_school_courses(id_school: int) -> ResponseReturnValue:
    """
    Fetch all courses for a given school ID.

    Args:
        id_school (int): The ID of the school to fetch courses for.

    Returns:
        JSON response with the courses related to the specified school.
    """
    courses = Course.to_dict_all(db.session.get(School, id_school).courses)
    return data_response(courses)


# Endpoint: /backend/data/subjects
@data.route("/subjects", methods=["GET"])
@jwt_required(optional=True)
def fetch_user_subjects() -> ResponseReturnValue:
    """
    Fetch the subjects associated with the current user if authenticated,
    otherwise fetch subjects for 'Cornell University'.

    Returns:
        JSON response with the subjects.
    """
    user = get_current_user()
    if user:
        # If user is logged in, get their school
        school = user.school
    else:
        # If no user is logged in, default to Cornell University
        school = db.session.query(School).filter_by(name="Cornell University").first()

    # Call another endpoint to fetch subjects for the school
    response = internal_request(
        url_for("backend.data.fetch_school_subjects", id_school=school.id), method="GET"
    )
    return response


# Endpoint: /backend/data/school/<id_school>/subjects
@data.route("/school/<int:id_school>/subjects", methods=["GET"])
def fetch_school_subjects(id_school: int) -> ResponseReturnValue:
    """
    Fetch all subjects for a given school ID.

    Args:
        id_school (int): The ID of the school to fetch subjects for.

    Returns:
        JSON response with the subjects related to the specified school.
    """
    AcademicField.query.filter_by(school_id=id_school).all()
    subjects = AcademicField.to_dict_all(
        db.session.query(AcademicField).filter_by(school_id=id_school).all()
    )
    return data_response(subjects)


# Endpoint: /backend/data/majors
@data.route("/majors", methods=["GET"])
@jwt_required(optional=True)
def fetch_user_majors() -> ResponseReturnValue:
    """
    Fetch the majors associated with the current user if authenticated,
    otherwise fetch majors for 'Cornell University'.

    Returns:
        JSON response with the majors.
    """
    user = get_current_user()
    if user:
        # Fetch user's school if authenticated
        school = user.school
    else:
        # Default to Cornell University if not authenticated
        school = db.session.query(School).filter_by(name="Cornell University").first()

    # Call another endpoint to fetch majors for the school
    response = internal_request(
        url_for("backend.data.fetch_school_majors", id_school=school.id), method="GET"
    )
    return response


# Endpoint: /backend/data/school/<id_school>/majors
@data.route("/school/<int:id_school>/majors", methods=["GET"])
def fetch_school_majors(id_school: int) -> ResponseReturnValue:
    """
    Fetch all majors for a given school ID.

    Args:
        id_school (int): The ID of the school to fetch majors for.

    Returns:
        JSON response with the majors related to the specified school.
    """
    majors = Major.to_dict_all(
        db.session.query(Major).filter_by(school_id=id_school).all()
    )
    return data_response(majors)


# Endpoint: /backend/data/methods
@data.route("/methods", methods=["GET"])
def fetch_methods() -> ResponseReturnValue:
    """
    Fetch all supported methods.

    Returns:
        JSON response with the supported methods.
    """
    methods = Method.to_dict_all(
        db.session.query(Method).filter_by(supported=True).all()
    )
    return data_response(methods)


# Endpoint: /backend/data/intervals
@data.route("/intervals", methods=["GET"])
def fetch_intervals() -> ResponseReturnValue:
    """
    Fetch all time intervals.

    Returns:
        JSON response with the time intervals.
    """
    time_intervals = TimeInterval.to_dict_all(db.session.query(TimeInterval).all())
    return data_response(time_intervals)


# Endpoint: /backend/data/notifications
@data.route("/notifications", methods=["GET"])
def fetch_user_notifications() -> ResponseReturnValue:
    """
    Fetch notifications for the current user.

    Returns:
        JSON response with the user's notifications or an error if user is not found.
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", ErrorType.USER_NOT_FOUND)

    # Collect notifications for the logged-in user
    notifications = []
    if user:
        notifications = Notification.to_dict_all(user.notifications)

    return data_response(notifications)
