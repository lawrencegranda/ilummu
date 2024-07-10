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
from flask_jwt_extended import jwt_required, exceptions, get_jwt_identity
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
        print(f"fetch_data: {status}")
        return []

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
    subjects.sort(key=lambda d: d["name"])

    methods = fetch_data(url_for("backend.data.fetch_methods"), "GET")
    methods.sort(key=lambda d: d["name"])

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
    majors.sort(key=lambda d: d["name"])

    return render_template("signup.html", login=False, majors=majors)


# Endpoint: /dashboard
@frontend.route("/dashboard")
@jwt_required()
def dashboard():
    subjects = fetch_data(url_for("backend.data.fetch_user_subjects"), "GET")
    subjects.sort(key=lambda d: d["name"])

    methods = fetch_data(url_for("backend.data.fetch_methods"), "GET")
    methods.sort(key=lambda d: d["name"])

    time_intervals = fetch_data(url_for("backend.data.fetch_intervals"), "GET")

    questions = fetch_data(url_for("backend.data.fetch_questions"), "GET")
    questions.sort(key=lambda d: (d["solved"], d["created_at"]))

    notifications = fetch_data(url_for("backend.data.fetch_user_notifications"), "GET")
    notifications.sort(key=lambda d: d["created_at"])

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


# Endpoint: /question/<id_question>
@question.route("/<int:id_question>")
@jwt_required(optional=True)
def fetch_question(id_question):
    subjects = fetch_data(url_for("backend.data.fetch_user_subjects"), "GET")
    subjects.sort(key=lambda d: d["name"])

    methods = fetch_data(url_for("backend.data.fetch_methods"), "GET")
    methods.sort(key=lambda d: d["name"])

    time_intervals = fetch_data(url_for("backend.data.fetch_intervals"), "GET")

    question = fetch_data(
        url_for("backend.data.get_question", id_question=id_question), "GET"
    )[0]

    if not get_jwt_identity():
        is_author = False
        made_offer = False
        offer_made = None
        accepted_offer = False
        offer_accepted = None
        offers = []

    else:
        is_author = fetch_data(
            url_for("backend.data.is_question_author", id_question=id_question), "GET"
        )[0]
        made_offer = False
        offer_made = None
        accepted_offer = False
        offer_accepted = None
        offers = []

    notifications = fetch_data(url_for("backend.data.fetch_user_notifications"), "GET")
    notifications.sort(key=lambda d: d["created_at"])

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
