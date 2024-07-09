from flask import (
    Flask,
    render_template,
    request,
    Blueprint,
    jsonify,
    current_app,
    url_for,
)
from http import HTTPStatus
from edify import db, bcrypt
from typing import Any
from flask_jwt_extended import jwt_required, current_user, exceptions
from edify.utils.decorators import no_token_allowed
from edify.models import *
import time
from edify.utils.utils import internal_request

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def fetch_data(url, method="GET"):
    data, status = internal_request(url, method)

    if status != HTTPStatus.OK:
        return None

    return data.get("data", [])


# -----------------------------------------------------------------------------
# Route Blueprint
# -----------------------------------------------------------------------------
# Endpoint: /
frontend = Blueprint("frontend", __name__, url_prefix="/")
# Endpoint: /question/
question = Blueprint("question", __name__, url_prefix="/question")


# -----------------------------------------------------------------------------
# Blueprint Endpoints (frontend)
# -----------------------------------------------------------------------------


# Endpoint: /
@frontend.route("/")
def index():
    subjects = fetch_data(url_for("backend.data.fetch_user_subjects"), "GET")
    methods = fetch_data(url_for("backend.data.fetch_methods"), "GET")
    time_intervals = fetch_data(url_for("backend.data.fetch_intervals"), "GET")

    return render_template(
        "/home.html",
        subjects=subjects,
        methods=methods,
        time_intervals=time_intervals,
    )


# Endpoint: /login
@frontend.route("/login")
@no_token_allowed
def login():
    return render_template("signup.html", login=True)


# Endpoint: /signup
@frontend.route("/signup")
@no_token_allowed
def signup():
    majors = fetch_data(url_for("backend.data.fetch_user_majors"), "GET")

    return render_template("signup.html", login=False, majors=majors)


# Endpoint: /dashboard
@frontend.route("/dashboard")
def dashboard():
    subjects = fetch_data(url_for("backend.data.fetch_user_subjects"), "GET")
    methods = fetch_data(url_for("backend.data.fetch_methods"), "GET")
    time_intervals = fetch_data(url_for("backend.data.fetch_intervals"), "GET")

    notifications = None
    questions = None

    return render_template(
        "dashboard.html",
        subjects=subjects,
        methods=methods,
        time_intervals=time_intervals,
        notifications=notifications,
        questions=questions,
    )


# -----------------------------------------------------------------------------
# Blueprint Endpoints (question)
# -----------------------------------------------------------------------------


# Endpoint: /question/<id_qstn>
@question.route("/<int:id_qstn>")
def fetch_question(id_qstn):
    subjects = fetch_data(url_for("backend.data.fetch_user_subjects"), "GET")
    methods = fetch_data(url_for("backend.data.fetch_methods"), "GET")
    time_intervals = fetch_data(url_for("backend.data.fetch_intervals"), "GET")

    question = None

    notifications = None

    return render_template(
        "view.html",
        subjects=subjects,
        methods=methods,
        time_intervals=time_intervals,
        notifications=notifications,
        q=question,
        is_author=is_author,
        made_offer=made_offer,
        offer_made=offer_made,
        accepted_offer=accepted_offer,
        offer_accepted=offer_accepted,
        offers=offers,
    )


# -----------------------------------------------------------------------------
# Children Blueprints
# -----------------------------------------------------------------------------
frontend.register_blueprint(question)
