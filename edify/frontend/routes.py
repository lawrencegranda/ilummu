# Standard Library imports
import re
import time
from http import HTTPStatus
from typing import Any, Dict, List, Optional

# Third-Party Framework imports
from flask import (
    Blueprint,
    Flask,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask import typing as flask_typing
from flask_jwt_extended import (
    exceptions,
    get_jwt_identity,
    jwt_required,
    unset_jwt_cookies,
)
from webargs import fields, validate
from webargs.flaskparser import use_args

# Local Application imports
from edify import bcrypt, db
from edify.models import *
from edify.utils.decorators import no_token_allowed
from edify.utils.utils import error_response, internal_request


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def fetch_data(url: str, method: str = "GET") -> List[Any]:
    """
    Fetch data from the backend API.

    Parameters:
    - url (str): Endpoint to fetch data from.
    - method (str): HTTP method to use (default is "GET").

    Returns:
    - List: Parsed data returned from the backend or an empty list on error.
    """
    response = internal_request(url, method)

    # Parse the response
    data, status = response.get_json(), response.status_code

    if status != HTTPStatus.OK:
        print(f"fetch_data: {status}")
        return []

    return data.get("data", [])


def get_user() -> Optional[Dict[str, Any]]:
    """
    Retrieve the current user's details.

    Returns:
    - Optional[Dict]: User data if authenticated, else None.
    """
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
def index() -> flask_typing.ResponseReturnValue:
    """
    Homepage route. Redirects users based on their authentication status.

    Returns:
    - str: Rendered homepage or dashboard template.
    """
    user = get_user()

    if user:
        return dashboard()
    else:
        return home()


# Endpoint: /home
@frontend.route("/home")
@jwt_required(optional=True)
def home() -> flask_typing.ResponseReturnValue:
    """
    Home route displaying user-related data.

    Returns:
    - str: Rendered home template.
    """
    subjects = fetch_data(url_for("backend.data.fetch_user_subjects"), "GET")
    subjects.sort(key=lambda d: d["name"])

    methods = fetch_data(url_for("backend.data.fetch_methods"), "GET")
    methods.sort(key=lambda d: d["name"])

    time_intervals = fetch_data(url_for("backend.data.fetch_intervals"), "GET")

    return render_template(
        "/home.jinja",
        subjects=subjects,
        methods=methods,
        time_intervals=time_intervals,
    )


# Endpoint: /login
@frontend.route("/login")
@no_token_allowed
def login() -> flask_typing.ResponseReturnValue:
    """
    Login route for rendering the login form.

    Returns:
    - str: Rendered login/signup template.
    """
    return render_template("signup.jinja", login=True)


# Endpoint: /signup
@frontend.route("/signup")
@no_token_allowed
def signup() -> flask_typing.ResponseReturnValue:
    """
    Signup route that fetches majors and renders the signup form.

    Returns:
    - str: Rendered signup template.
    """
    majors = fetch_data(url_for("backend.data.fetch_user_majors"), "GET")
    majors.sort(key=lambda d: d["name"])

    print(majors)

    return render_template("signup.jinja", login=False, majors=majors)


# Endpoint: /logout
@frontend.route("/logout")
def logout() -> flask_typing.ResponseReturnValue:
    """
    Logout route that invalidates the user's session.

    Returns:
    - str: Redirect to the login page.
    """
    response = internal_request(url_for("backend.user.logout"), method="POST")

    # If the backend logout was successful, clear the cookies and redirect
    if response.status_code != HTTPStatus.OK:
        print("Unsuccessful logout.")

    response = redirect(url_for("frontend.login"))
    unset_jwt_cookies(response)
    return response


# Endpoint: /dashboard
@frontend.route("/dashboard")
@jwt_required(optional=True)
def dashboard() -> flask_typing.ResponseReturnValue:
    """
    Dashboard route displaying user data and related questions.

    Returns:
    - str: Rendered dashboard template with user data.
    """
    user = get_user()

    subjects = fetch_data(url_for("backend.data.fetch_user_subjects"), "GET")
    subjects.sort(key=lambda d: d["name"])

    methods = fetch_data(url_for("backend.data.fetch_methods"), "GET")
    methods.sort(key=lambda d: d["name"])

    time_intervals = fetch_data(url_for("backend.data.fetch_intervals"), "GET")

    notifications = fetch_data(url_for("backend.data.fetch_user_notifications"), "GET")
    notifications.sort(key=lambda d: d["created_at"])

    return render_template(
        "dashboard.jinja",
        subjects=subjects,
        methods=methods,
        time_intervals=time_intervals,
        user=user,
        question_list=list_questions("", ""),
    )


@frontend.route("/list", methods=["GET"])
@jwt_required(optional=True)
@use_args(
    {
        "field": fields.Str(required=True),
        "search": fields.Str(required=False),
    }
)
def question_list(args) -> flask_typing.ResponseReturnValue:
    """
    List questions based on filter criteria. Route endpoint.

    Parameters:
    - field (str): Subject to filter by.
    - search (str): Search text.

    Returns:
    - str: Rendered question list template.
    """

    return list_questions(args.get("field", ""), args.get("search", ""))


@jwt_required(optional=True)
def list_questions(field: str, search: str) -> str:
    """
    List questions based on filter criteria.

    Parameters:
    - field (str): Subject to filter by.
    - search (str): Search text.

    Returns:
    - str: Rendered question list template.
    """
    # Fetch questions from the backend
    questions = fetch_data(url_for("backend.data.fetch_questions"), "GET")

    field = field.strip()
    search = search.strip()

    # Filter questions based on field/subject
    if field:
        questions = filter_list(questions, "subject", field)

    # Filter questions based on search text if provided
    if search:
        questions_code = filter_list(questions, "course_code", search)
        questions_course = filter_list(questions, "course_name", search)
        questions_request = filter_list(questions, "request", search)

        questions = [*questions_code, *questions_course, *questions_request]

    # Get current user
    user = get_user()

    if user:

        def is_author(d):
            result = fetch_data(
                url_for("backend.data.is_question_author", id_question=d["id"])
            )
            return result[0] if result else False

        def made_offer(d):
            result = fetch_data(
                url_for("backend.data.question_offer_made", id_question=d["id"])
            )
            return len(result) > 0

        # Only questions not solved, or authored or made an offer.
        questions = [
            q for q in questions if not q["solved"] or is_author(q) or made_offer(q)
        ]

        # Sorting the 'questions' list primarily by 'solved' status, then by the
        # author'sstatus, whether an offer was made, and finally by the creation date.
        questions.sort(
            key=lambda d: (
                d["solved"],
                not is_author(d),
                not made_offer(d),
                d["created_at"],
            )
        )

    else:
        # If not logged in, only unsolved
        questions = [q for q in questions if not q["solved"]]

        # Sort questions by creation date, ensuring unsolved are first
        questions.sort(key=lambda d: (d["solved"], d["created_at"]))

    return render_template("bases/question-list.jinja", questions=questions)


def filter_list(list: List[Dict], field: str, search: Optional[str]) -> List[Dict]:
    """
    Filters the list of dicts based on the provided field and search text.

    Parameters:
    - questions (List[Dict]): The list of questions to filter.
    - field (str): The field to filter by.
    - search (Optional[str]): The search text to filter questions.

    Returns:
    - List[Dict]: The filtered list of questions.
    """
    # Return all questions if no field is specified
    if not search or not search.strip():
        return questions

    filtered_questions = []

    # Split by non-alphanumeric characters and lowercase
    search_terms = re.findall(r"\b\w+\b", search.lower())

    for question in questions:
        # Append questions that constain all the words
        if all(term in question.get(field, "").lower() for term in search_terms):
            filtered_questions.append(question)

    return filtered_questions


# -----------------------------------------------------------------------------
# Blueprint Endpoints (question)
# -----------------------------------------------------------------------------


# Endpoint: /question/<id_question>
@question.route("/<int:id_question>")
@jwt_required(optional=True)
def fetch_question(id_question: int) -> flask_typing.ResponseReturnValue:
    """
    Retrieve a specific question by ID and related data.

    Parameters:
    - id_question (int): The ID of the question.

    Returns:
    - str: Rendered question detail template or error response.
    """
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

    # Initialize variables related to the question
    is_author = False
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

        if not offer_made:
            offer_made = None

    return render_template(
        "question.jinja",
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
