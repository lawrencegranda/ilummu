from flask import (
    Flask,
    render_template,
    Blueprint,
    jsonify,
    current_app,
    url_for,
    redirect,
    request,
)
from http import HTTPStatus
from edify import db, bcrypt
from typing import Any
from flask_jwt_extended import (
    jwt_required,
    exceptions,
    get_jwt_identity,
    unset_jwt_cookies,
)
from edify.utils.decorators import no_token_allowed
from edify.models import *
import time
from edify.utils.utils import internal_request, error_response
from webargs import fields, validate
from webargs.flaskparser import use_args

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def fetch_data(url, method="GET"):
    response = internal_request(url, method)

    # Parse the response
    data, status = response.get_json(), response.status_code

    if status != HTTPStatus.OK:
        print(f"fetch_data: {status}")
        return []

    return data.get("data", [])


def get_user():
    response = internal_request(url_for("backend.user.get_user"), "GET")

    return response.get_json()


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
@jwt_required(optional=True)
def index():
    user = get_user()

    if user:
        return dashboard()
    else:
        return home()


# Endpoint: /home
@frontend.route("/home")
@jwt_required(optional=True)
def home():
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

    print(majors)

    return render_template("signup.html", login=False, majors=majors)


# Endpoint: /logout
@frontend.route("/logout")
@jwt_required()
def logout():
    response = internal_request(url_for("backend.user.logout"), method="POST")

    # If the backend logout was successful, clear the cookies and redirect
    if response.status_code == HTTPStatus.OK:
        response = redirect(url_for("frontend.index"))
        unset_jwt_cookies(response)
        return response

    print("Unsuccessful logout.")

    return redirect(url_for("frontend.index"))


# Endpoint: /dashboard
@frontend.route("/dashboard")
@jwt_required(optional=True)
def dashboard():
    user = get_user()

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
        user=user,
        questions=questions,
    )


# Endpoint: /list
@frontend.route("/list", methods=["GET"])
@use_args({"field": fields.Str(required=False), "text": fields.Str(required=False)})
def question_list():
    # Trim all string values in args
    for key, value in args.items():
        if isinstance(value, str):
            args[key] = value.strip().lowe()

    questions = fetch_data(url_for("backend.data.fetch_questions"), "GET")

    if args["field"]:
        field = None
    else:
        field = None

    text = args["field"] if args["field"] else ""

    questions.sort(key=lambda d: (d["solved"], d["created_at"]))

    return render_template(
        "bases/question-list.html",
        questions=questions,
    )


# -----------------------------------------------------------------------------
# Blueprint Endpoints (question)
# -----------------------------------------------------------------------------


# Endpoint: /question/<id_question>
@question.route("/<int:id_question>")
@jwt_required(optional=True)
def fetch_question(id_question):
    user = get_user()

    subjects = fetch_data(url_for("backend.data.fetch_user_subjects"), "GET")
    subjects.sort(key=lambda d: d["name"])

    methods = fetch_data(url_for("backend.data.fetch_methods"), "GET")
    methods.sort(key=lambda d: d["name"])

    time_intervals = fetch_data(url_for("backend.data.fetch_intervals"), "GET")

    notifications = fetch_data(url_for("backend.data.fetch_user_notifications"), "GET")
    notifications.sort(key=lambda d: d["created_at"])

    question = fetch_data(
        url_for("backend.data.get_question", id_question=id_question), "GET"
    )

    if not question:
        return error_response("Not a valid question", HTTPStatus.NOT_FOUND)

    question = question[0]

    is_author = False
    made_offer = False
    offer_made = None
    offer_accepted = None
    offers = []

    if user:
        is_author = fetch_data(
            url_for("backend.data.is_question_author", id_question=id_question), "GET"
        )[0]

        if is_author:
            offers = fetch_data(
                url_for("backend.data.offers_received", id_question=id_question), "GET"
            )
            for offer in offers:
                if offer["status"] == OfferStatusEnum.ACCEPTED:
                    offer_accepted = offer

        offer_made = fetch_data(
            url_for("backend.data.question_offer_made", id_question=id_question), "GET"
        )

        if offer_made:
            made_offer = True
            offer_made = fetch_data(
                url_for("backend.data.question_offer_made", id_question=id_question),
                "GET",
            )
        else:
            offer_made = None

    return render_template(
        "question.html",
        subjects=subjects,
        methods=methods,
        time_intervals=time_intervals,
        notifications=notifications,
        user=user,
        question=question,
        is_author=is_author,
        offer_made=offer_made,
        offer_accepted=offer_accepted,
        offers=offers,
    )


# -----------------------------------------------------------------------------
# Children Blueprints
# -----------------------------------------------------------------------------
frontend.register_blueprint(question)
