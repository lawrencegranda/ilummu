"""Frontend routes and view functions for the Edify platform."""

# Standard Library imports
import io
import os
import re
from http import HTTPStatus
from typing import Any, Dict, List, Optional
from tempfile import mkdtemp
import urllib.request
from urllib.parse import quote

# Third-Party Framework imports
from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask.typing import ResponseReturnValue
from flask_jwt_extended import jwt_required, unset_jwt_cookies
from webargs import fields
from webargs.flaskparser import use_args
from werkzeug.utils import secure_filename

# Local Application imports
from edify.utils.constants import ErrorType, QuestionSchema
from edify.utils.decorators import no_token_allowed
from edify.utils.utils import error_response, internal_request


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def fetch_data(url: str, method: str = "GET") -> List[Any]:
    """
    Fetch data from the backend API.

    Parameters:
        url (str): Endpoint to fetch data from.
        method (str): HTTP method to use (default is "GET").

    Returns:
        List: Parsed data returned from the backend or an empty list on error.
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
        Optional[Dict]: User data if authenticated, else None.
    """
    response = internal_request(url_for("backend.user.get_user"), "GET").get_json()

    if response and isinstance(response, dict) and "user" in response:
        return response["user"]

    return None


def is_verified() -> bool:
    """Check if current user's email is verified."""
    response = internal_request(url_for("backend.user.is_verified"), "GET")
    return response.get_json() is True


def filter_list(dlist: List[Dict], field: str, search: Optional[str]) -> List[Dict]:
    """
    Filters the list of dicts based on the provided field and search text.

    Parameters:
        dlist (List[Dict]): The list to filter.
        field (str): The field to filter by.
        search (Optional[str]): The search text to filter list.

    Returns:
        List[Dict]: The filtered list of questions.
    """
    # Return all questions if no field is specified
    if not search or not search.strip():
        return dlist

    filtered_list = []

    # Split by non-alphanumeric characters and lowercase
    search_terms = re.findall(r"\b\w+\b", search.lower())

    for d in dlist:
        # Append questions that constain all the words
        if all(term in d.get(field, "").lower() for term in search_terms):
            filtered_list.append(d)

    return filtered_list


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

# PAGES             %------------------------------------------------------------------%


# Endpoint: /
@frontend.route("/")
@jwt_required(optional=True)
def index() -> ResponseReturnValue:
    """
    Homepage route. Redirects users based on their authentication status.

    Returns:
        str: Rendered homepage or dashboard template.
    """
    user = get_user()

    if user:
        return dashboard()

    return home()


# Endpoint: /home
@frontend.route("/home")
@jwt_required(optional=True)
def home() -> ResponseReturnValue:
    """
    Home route displaying user-related data.

    Returns:
        str: Rendered home template.
    """
    # Fetch the logged user if any, else None
    user = get_user()

    courses = fetch_data(url_for("backend.data.fetch_user_courses"), "GET")
    courses.sort(key=lambda d: d["code"])

    subjects = fetch_data(url_for("backend.data.fetch_user_subjects"), "GET")
    subjects.sort(key=lambda d: d["name"])

    methods = fetch_data(url_for("backend.data.fetch_methods"), "GET")
    methods.sort(key=lambda d: d["name"])

    time_intervals = fetch_data(url_for("backend.data.fetch_intervals"), "GET")

    return render_template(
        "/home.jinja",
        courses=courses,
        subjects=subjects,
        methods=methods,
        time_intervals=time_intervals,
        user=user,
    )


# Endpoint: /dashboard
@frontend.route("/dashboard")
@jwt_required(optional=True)
def dashboard() -> ResponseReturnValue:
    """
    Dashboard route displaying user data and related questions.

    Returns:
        str: Rendered dashboard template with user data.
    """
    user = get_user()

    if user and not is_verified():
        return email_verification()

    courses = fetch_data(url_for("backend.data.fetch_user_courses"), "GET")
    courses.sort(key=lambda d: d["code"])

    subjects = fetch_data(url_for("backend.data.fetch_user_subjects"), "GET")
    subjects.sort(key=lambda d: d["name"])

    methods = fetch_data(url_for("backend.data.fetch_methods"), "GET")
    methods.sort(key=lambda d: d["name"])

    time_intervals = fetch_data(url_for("backend.data.fetch_intervals"), "GET")

    return render_template(
        "dashboard.jinja",
        courses=courses,
        subjects=subjects,
        methods=methods,
        time_intervals=time_intervals,
        user=user,
        question_list=list_questions([], ""),
    )


# TOKENS            %------------------------------------------------------------------%


# Endpoint: /logout
@frontend.route("/logout")
def logout() -> ResponseReturnValue:
    """
    Logout route that invalidates the user's session.

    Returns:
        str: Redirect to the login page.
    """
    response = internal_request(url_for("backend.user.logout"), method="POST")

    # If the backend logout was successful, clear the cookies and redirect
    if response.status_code != HTTPStatus.OK:
        print("Unsuccessful logout.")

    response = redirect(url_for("frontend.home"))
    unset_jwt_cookies(response)
    return response


# Endpoint: /login
@frontend.route("/login")
@no_token_allowed
def login() -> ResponseReturnValue:
    """
    Login route for rendering the login form.

    Returns:
        str: Rendered login/signup template.
    """
    next_url = request.args.get("next_url", url_for("frontend.index"))
    http_method = request.args.get("http_method", "GET")

    return render_template(
        "signup.jinja", login=True, next_url=next_url, http_method=http_method
    )

# Endpoint: /signup
@frontend.route("/signup")
@no_token_allowed
def signup() -> ResponseReturnValue:
    """
    Signup route that fetches majors and renders the signup form.

    Returns:
        str: Rendered signup template.
    """
    majors = fetch_data(url_for("backend.data.fetch_user_majors"), "GET")
    majors.sort(key=lambda d: d["name"])

    # Google OAuth URL
    oauth_url = url_for("backend.oauth.login", _external=True)

    next_url = request.args.get("next_url", url_for("frontend.index"))
    http_method = request.args.get("http_method", "GET")

    return render_template(
        "signup.jinja",
        login=False,
        majors=majors,
        next_url=next_url,
        http_method=http_method,
        oauth_url=oauth_url,
    )


# QUESTION CREATION %------------------------------------------------------------------%


# Endpoint: /store_question
@frontend.route("/store_question", methods=["POST"])
@use_args(QuestionSchema, location="form")
@jwt_required(optional=True)
def store_question(args) -> ResponseReturnValue:
    """
    Store question data in session and handle file uploads.

    Returns:
        Response: Redirect to verification or question submission.
    """
    # Temporarily store the question data in the session
    session["temp_question"] = args

    # Retrive the file if any
    image_file = request.files.get("image", default=None)

    if image_file:
        if "temp_dir" not in session or not os.path.isdir(session["temp_dir"]):
            # Create a temporary directory
            temp_dir = mkdtemp()
            session["temp_dir"] = temp_dir

        # Secure the filename and save to the temp directory
        filename = secure_filename(image_file.filename)
        filepath = os.path.join(session["temp_dir"], filename)
        image_file.save(filepath)

        # Store the file path in the session
        session["temp_file"] = filepath

    # If the user is authenticated, create the question inmidiately.
    if get_user():
        return submit_question_after_login()

    # Return the data endpoint
    return (
        jsonify(
            {
                "next_url": quote(
                    url_for(
                        "frontend.email_verification",
                        next_url=url_for("frontend.submit_question_after_login"),
                        http_method="POST",
                    )
                ),
                "http_method": "GET",
            }
        ),
        HTTPStatus.OK,
    )


# Endpoint: /submit_question_after_login
@frontend.route("/submit_question_after_login", methods=["POST"])
@jwt_required()
def submit_question_after_login() -> ResponseReturnValue:
    """
    Submit stored question data after user authentication.

    Returns:
        Response: Result of question submission to backend.
    """
    # Retrieve the question data and file from the session
    data = session.pop("temp_question", None)
    file_path = session.pop("temp_file", None)

    if not data:
        return error_response(
            "No question data found in session.", ErrorType.BAD_REQUEST
        )

    # Prepare the form data
    question_data = data.copy()
    file = None

    # Attach the file if it exists
    if file_path:
        try:
            # Flask test client format
            with open(file_path, "rb") as f:
                file = (io.BytesIO(f.read()), os.path.basename(file_path))
        except (IOError, OSError) as e:
            print(f"Failed to read file from path: {e}")

    # Submit the question using the existing endpoint
    # Create a request to submit the question to /backend/question/new
    response = internal_request(
        url_for("backend.question.create_question"),
        method="POST",
        data=question_data,
        is_form=True,
        file=file,
    )

    return response


# REIDRECT HANDLER  %------------------------------------------------------------------%


# Endpoint: /redirect_handler
@frontend.route("/redirect_handler")
def redirect_handler():
    """
    Handle redirects with custom URL and HTTP method.

    Returns:
        Response: Rendered template with redirect parameters.
    """
    # Get `next_url` and `http_method` from query parameters
    next_url = request.args.get("next_url", url_for("frontend.dashboard"))
    http_method = request.args.get("http_method", "GET").upper()

    # Render the template with the redirection logic
    return render_template(
        "redirect_handler.jinja", next_url=next_url, http_method=http_method
    )


# PASSWORD RESET    %------------------------------------------------------------------%


# Endpoint: /forgot-password
@frontend.route("/forgot-password")
def forgot_password() -> ResponseReturnValue:
    """
    Forgot password route.

    Returns:
        str: Rendered route.
    """
    next_url = request.args.get("next_url", url_for("frontend.index"))
    http_method = request.args.get("http_method", "GET")

    return render_template(
        "/forgot_password.jinja", next_url=next_url, http_method=http_method
    )


# Endpoint: /reset-password
@frontend.route("/reset-password")
def reset_password() -> ResponseReturnValue:
    """
    Reset password route.

    Returns:
        str: Rendered route.
    """
    token = request.args.get("token", "")

    if not token:
        forgot_password()

    success = (
        internal_request(url_for("backend.user.check_token", token=token)).status_code
        == HTTPStatus.OK
    )

    if not success:
        return render_template("/invalid_reset.jinja")

    return render_template("/reset_password.jinja", token=token)


# VERIFY EMAIL      %------------------------------------------------------------------%


# Endpoint: /email-verification
@frontend.route("/email-verification")
@jwt_required()
def email_verification(
    next_url: str = None, http_method: str = None
) -> ResponseReturnValue:
    """
    Route to verify email.

    Returns:
        str: Rendered route.
    """
    user = get_user()

    # Check if next_url and http_method are provided in the request
    if next_url is None:
        next_url = request.args.get("next_url", url_for("frontend.dashboard"))

    if http_method is None:
        http_method = request.args.get("http_method", "GET")

    if user and user["mail_is_verified"] is True:
        # Use the redirect handler template
        return redirect(
            url_for(
                "frontend.redirect_handler", next_url=next_url, http_method=http_method
            )
        )

    return render_template(
        "/email_verification.jinja", next_url=next_url, http_method=http_method
    )


# Endpoint: /verify-email
@frontend.route("/verify-email")
def verify_email() -> ResponseReturnValue:
    """
    Email verification.

    Returns:
        str: Rendered route.
    """
    token = request.args.get("token", "")

    if not token:
        return render_template("/invalid_verification.jinja")

    success = (
        internal_request(
            url_for("backend.user.check_auth_token", token=token)
        ).status_code
        == HTTPStatus.OK
    )

    if not success:
        return render_template("/invalid_verification.jinja")

    return dashboard()


# QUESTION SEARCH   %------------------------------------------------------------------%


# Endpoint: /list
@frontend.route("/list", methods=["GET"])
@jwt_required(optional=True)
@use_args(
    {
        "fields": fields.List(fields.Str(), required=False),
        "search": fields.Str(required=False),
    },
    location="query",
)
def question_list(args) -> ResponseReturnValue:
    """
    List questions based on filter criteria. Route endpoint.

    Parameters:
        fields (List[str]): Subjects to filter by.
        search (str): Search text.

    Returns:
        str: Rendered question list template.
    """
    return list_questions(args.get("fields", []), args.get("search", ""))


@jwt_required(optional=True)
def list_questions(field_lst: List[str], search: str) -> str:
    """
    List questions based on filter criteria.

    Parameters:
        field_lst (List[str]): Subjects to filter by.
        search (str): Search text.

    Returns:
        str: Rendered question list template.
    """
    # Fetch questions from the backend
    qtns = fetch_data(url_for("backend.question.get_all"), "GET")
    search = search.strip()

    # Initialize the questions slide
    questions = []

    # Get all if empty
    if not field_lst:
        questions = qtns

    # Filter questions based on field/subject
    for field in field_lst:
        questions.extend(filter_list(qtns, "subject_code", field.strip()))

    # Filter questions based on search text if provided
    if search:
        questions_code = filter_list(questions, "course_code", search)
        questions_course = filter_list(questions, "course_name", search)
        questions_request = filter_list(questions, "request", search)

        questions = [*questions_code, *questions_course, *questions_request]

    # Remove duplicates
    questions = {q["id"]: q for q in questions}.values()

    # Get current user
    user = get_user()

    if user:
        # Only questions not solved, or authored or made an offer.
        questions = [
            d
            for d in questions
            if not d["solved"] or d["is_author"] or (d["offer_made"] is not None)
        ]

        # Sorting the 'questions' list primarily by 'solved' status, then by the
        # author's status, whether an offer was made, and finally by the creation date.
        questions.sort(
            key=lambda d: (
                d["solved"],
                not d["is_author"],
                not (d["offer_made"] is not None),
                d["seconds_ago"],
            )
        )

    else:
        # If not logged in, only unsolved
        questions = [d for d in questions if not d["solved"]]

        # Sort questions by creation date, ensuring unsolved are first
        questions.sort(key=lambda d: (d["solved"], d["seconds_ago"]))

    return render_template("bases/question-list.jinja", questions=questions)


# -----------------------------------------------------------------------------
# Blueprint Endpoints (question)
# -----------------------------------------------------------------------------


# Endpoint: /question/<id_question>
@question.route("/<int:id_question>")
@jwt_required(optional=True)
def fetch_question(id_question: int) -> ResponseReturnValue:
    """
    Retrieve a specific question by ID and related data.

    Parameters:
        id_question (int): The ID of the question.

    Returns:
        str: Rendered question detail template or error response.
    """
    user = get_user()

    courses = fetch_data(url_for("backend.data.fetch_user_courses"), "GET")
    courses.sort(key=lambda d: d["code"])

    subjects = fetch_data(url_for("backend.data.fetch_user_subjects"), "GET")
    subjects.sort(key=lambda d: d["name"])

    methods = fetch_data(url_for("backend.data.fetch_methods"), "GET")
    methods.sort(key=lambda d: d["name"])

    time_intervals = fetch_data(url_for("backend.data.fetch_intervals"), "GET")

    question_obj = fetch_data(
        url_for("backend.question.get", id_question=id_question), "GET"
    )

    if not question_obj:
        return error_response("Not a valid question", HTTPStatus.NOT_FOUND)

    question_obj = question_obj[0]

    question_obj["user"]["username"] = (
        "You" if question_obj["is_author"] else question_obj["user"]["username"]
    )

    question_obj["is_image"] = False
    if question_obj["image_url"]:
        # Fetch the MIME type of question
        try:
            req = urllib.request.Request(question_obj["image_url"], method="HEAD")
            with urllib.request.urlopen(req) as response:
                question_obj["is_image"] = response.headers.get(
                    "Content-Type", ""
                ).startswith("image")
        except urllib.error.URLError as e:
            print(f"Error fetching MIME type: {e}")

    return render_template(
        "question.jinja",
        courses=courses,
        subjects=subjects,
        methods=methods,
        time_intervals=time_intervals,
        user=user,
        question=question_obj,
    )


# -----------------------------------------------------------------------------
# Children Blueprints
# -----------------------------------------------------------------------------


# List of endpoints that exclude email verification
verification_excluded_endpoints = [
    "frontend.email_verification",
    "frontend.logout",
    "frontend.store_question",
]


@frontend.before_request
def ensure_verified():
    """
    Before request handler to ensure user's email is verified.

    Returns:
        Optional[Response]: Redirect to verification page if needed.
    """
    # Only apply email verification logic for specific endpoints
    if request.endpoint in verification_excluded_endpoints:
        return None

    # New user
    user = get_user()

    if request.method == "POST" or not user or user["mail_is_verified"] is True:
        return None

    return email_verification(http_method=request.method, next_url=request.url)


# -----------------------------------------------------------------------------
# Children Blueprints
# -----------------------------------------------------------------------------
frontend.register_blueprint(question)
