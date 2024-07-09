from flask import Flask, render_template, request, Blueprint, jsonify, current_app
from http import HTTPStatus
from edify import db, bcrypt
from typing import Any
from flask_jwt_extended import jwt_required, current_user, exceptions
from edify.utils.decorators import no_token_allowed

import time

# -----------------------------------------------------------------------------
# Route Declaration
# -----------------------------------------------------------------------------
# Endpoint: /
frontend = Blueprint("frontend", __name__, url_prefix="/")

subjects = [
    {"value": "cals", "name": "Agriculture and Life Sciences"},
    {"value": "aap", "name": "Architecture, Art and Planning"},
    {"value": "as", "name": "Arts and Sciences"},
    {"value": "dyson", "name": "Dyson"},
    {"value": "engineering", "name": "Engineering"},
    {"value": "human-ecology", "name": "Human Ecology"},
    {"value": "ilr", "name": "Industrial and Labor Relations"},
    {"value": "public-policy", "name": "Public Policy"},
]

methods = [
    {"value": "text-message", "name": "Text Message"},
    {"value": "voice-call", "name": "Voice Call"},
    {"value": "video-call", "name": "Video Call"},
    {"value": "photo-explanation", "name": "Photo Explanation"},
]

time_intervals = {
    5: {"value": 5, "name": "less than 5 min", "shortname": "<5 min"},
    10: {"value": 10, "name": "about 10 min", "shortname": "~10 min"},
    20: {"value": 20, "name": "about 20 min", "shortname": "~20 min"},
    30: {"value": 30, "name": "about 30 min", "shortname": "~30 min"},
    45: {"value": 45, "name": "about 45 min", "shortname": "~45 min"},
    60: {"value": 60, "name": "about 1 hour", "shortname": "~1 hour"},
    90: {"value": 90, "name": "about 1.5 hours", "shortname": "~1.5 hours"},
    120: {"value": 120, "name": "about 2 hours", "shortname": "~2 hours"},
    999: {"value": 999, "name": "over 2 hours", "shortname": ">2 hours"},
}

users = {
    1: {
        "id": 1,
        "name": "OrangeJuice",
        "major": "Computer Science",
        "year": "Freshman",
        "rating": 3.7,
    },
    2: {
        "id": 2,
        "name": "AppleJuice",
        "major": "Information Science",
        "year": "Sophomore",
        "rating": 4.5,
    },
    3: {
        "id": 3,
        "name": "GuavaJuice",
        "major": "Economics",
        "year": "Junior",
        "rating": 5,
    },
    4: {
        "id": 4,
        "name": "MangoJuice",
        "major": "AEM",
        "year": "Senior",
        "rating": 2,
    },
    5: {
        "id": 5,
        "name": "PearJuice",
        "major": "Mechanical Engineering",
        "year": "Senior",
        "rating": None,
    },
    6: {
        "id": 6,
        "name": "BerryJuice",
        "major": "Engineering Physics",
        "year": "Junior",
        "rating": 4.3,
    },
}

import json

with open("edify/static/majors.json") as f:
    majors = json.load(f)["majors"]


def get_questions():
    question_one = {
        "id": 1,
        "solved": False,
        "subject": "Engineering",
        "number": "CS 2800",
        "name": "Discrete Math",
        "solve-time": 10,
        "request": "How to I transition from a NFA to a DFA?",
        "date": "06.01.2024",
        "time": "11:17pm",
        "time-ago": "Yesterday",
        "price": 2.5,
        "method": "Text message",
        "user_id": 1,
    }

    question_two = {
        "id": 2,
        "solved": False,
        "subject": "Engineering",
        "number": "CS 3110",
        "name": "Functional Programming",
        "solve-time": 5,
        "request": "How do I curry a function?",
        "date": "05.26.2024",
        "time": "7:47am",
        "time-ago": "A week ago",
        "price": 2,
        "method": "Text message",
        "user_id": 4,
    }

    question_three = {
        "id": 3,
        "solved": False,
        "subject": "Dyson",
        "number": "AEM 2200",
        "name": "Business Man and Org",
        "solve-time": 20,
        "request": "How do I create a SWOT analysis?",
        "date": "06.02.2024",
        "time": "5:28pm",
        "time-ago": "2 min ago",
        "price": 5.0,
        "method": "Video call",
        "user_id": 2,
    }

    question_four = {
        "id": 4,
        "solved": False,
        "subject": "Engineering",
        "number": "MATH 2940",
        "name": "Linear Algebra for Engineers",
        "solve-time": 45,
        "request": """Linear Combinations, Homogeneous Systems 3.57. Write v as a linear combination of U1, U2, U3, where U1 = (4,-9,2), U2 = (1,2,-1), U3 = (1,4,2): (a) V = (1,3,2), U = (1,2,1), U2 = (2,6,5), U3 = (1,7,8): (b) V = (1,4,6), U = (2,3,5), U2 = (3,5,8). 3.58 Let U1 = (1,1,2), U2 = (1,3,-2), U3 = (4,-2,-1) in R^3. Show that U1, U2, U3 are orthogonal, and write V as a linear combination of U1, U2, U3, where (a) V = (5,3,9), (b) V = (1,-3,3), (c) V = (1,1,1) (Hint: Use Fourier coefficients). 3.59 Find the dimension and a basis of the general solution W of each of the following homogeneous systems: (a) x + 2y = 0, (b) x + 2y - 3z = 0, (c) x + 2y + 3z + w = 0, (d) 2x + y + 2z = 0, (e) 2x + 4y + 7z + 4w = 0, (f) x + y + 4 = 0, (g) 3x - 4y = 0, (h) 3x + 6y + 10z + 5w = 0. 3.60 Find the dimension and basis of the general solution W of each of the following systems: (a) x + 3y + 2z - w = 0, (b) 2x + 4y + 3z + 2w = 0, (c) 2x + 6y + 5z + x5 = 0, (d) 5x + 10y - 3z + 14w = 0, (e) 11x + 12y + 13z + 14w = 0, (f) 5x + 10y + 3z + 14w = 0. Echelon Matrices, Row Canonical Form 3.61 Reduce each of the following matrices to echelon form and then to row canonical form: 1 2 0 -3 (b) 1 0 0 1 3.62 Reduce each of the following matrices to echelon form and then to row canonical form: 1 9 0 1 (b) 1 0 0 1 3.63 Using only 0's and 1's, list all possible 2 x 2 matrices in row canonical form. 3.64 Using only 0's and 1's, find the number n of possible 3 x 3 matrices in row canonical form.""",
        "date": "05.31.2024",
        "time": "6:00pm",
        "time-ago": "Two days ago",
        "price": 4.25,
        "method": "Voice call",
        "user_id": 5,
    }

    question_five = {
        "id": 5,
        "solved": True,
        "subject": "Engineering",
        "number": "CS 2800",
        "name": "Discrete Math",
        "solve-time": 10,
        "request": "How to I transition from a NFA to a DFA?",
        "date": "06.01.2024",
        "time": "11:17pm",
        "time-ago": "Yesterday",
        "price": 2.5,
        "method": "Text message",
        "user_id": 1,
    }

    question_six = {
        "id": 6,
        "solved": True,
        "subject": "Engineering",
        "number": "CS 3110",
        "name": "Functional Programming",
        "solve-time": 5,
        "request": "How do I curry a function?",
        "date": "05.26.2024",
        "time": "7:47am",
        "time-ago": "A week ago",
        "price": 2,
        "method": "Text message",
        "user_id": 4,
    }

    question_seven = {
        "id": 7,
        "solved": True,
        "subject": "Dyson",
        "number": "AEM 2200",
        "name": "Business Man and Org",
        "solve-time": 20,
        "request": "How do I create a SWOT analysis?",
        "date": "06.02.2024",
        "time": "5:28pm",
        "time-ago": "2 min ago",
        "price": 5.0,
        "method": "Video call",
        "user_id": 2,
    }

    question_eight = {
        "id": 8,
        "solved": True,
        "subject": "Engineering",
        "number": "MATH 2940",
        "name": "Linear Algebra for Engineers",
        "solve-time": 45,
        "request": """Linear Combinations, Homogeneous Systems 3.57. Write v as a linear combination of U1, U2, U3, where U1 = (4,-9,2), U2 = (1,2,-1), U3 = (1,4,2): (a) V = (1,3,2), U = (1,2,1), U2 = (2,6,5), U3 = (1,7,8): (b) V = (1,4,6), U = (2,3,5), U2 = (3,5,8). 3.58 Let U1 = (1,1,2), U2 = (1,3,-2), U3 = (4,-2,-1) in R^3. Show that U1, U2, U3 are orthogonal, and write V as a linear combination of U1, U2, U3, where (a) V = (5,3,9), (b) V = (1,-3,3), (c) V = (1,1,1) (Hint: Use Fourier coefficients). 3.59 Find the dimension and a basis of the general solution W of each of the following homogeneous systems: (a) x + 2y = 0, (b) x + 2y - 3z = 0, (c) x + 2y + 3z + w = 0, (d) 2x + y + 2z = 0, (e) 2x + 4y + 7z + 4w = 0, (f) x + y + 4 = 0, (g) 3x - 4y = 0, (h) 3x + 6y + 10z + 5w = 0. 3.60 Find the dimension and basis of the general solution W of each of the following systems: (a) x + 3y + 2z - w = 0, (b) 2x + 4y + 3z + 2w = 0, (c) 2x + 6y + 5z + x5 = 0, (d) 5x + 10y - 3z + 14w = 0, (e) 11x + 12y + 13z + 14w = 0, (f) 5x + 10y + 3z + 14w = 0. Echelon Matrices, Row Canonical Form 3.61 Reduce each of the following matrices to echelon form and then to row canonical form: 1 2 0 -3 (b) 1 0 0 1 3.62 Reduce each of the following matrices to echelon form and then to row canonical form: 1 9 0 1 (b) 1 0 0 1 3.63 Using only 0's and 1's, list all possible 2 x 2 matrices in row canonical form. 3.64 Using only 0's and 1's, find the number n of possible 3 x 3 matrices in row canonical form.""",
        "date": "05.31.2024",
        "time": "6:00pm",
        "time-ago": "Two days ago",
        "price": 4.25,
        "method": "Voice call",
        "user_id": 5,
    }

    question_nine = {
        "id": 9,
        "solved": True,
        "subject": "Engineering",
        "number": "CS 2800",
        "name": "Discrete Math",
        "solve-time": 10,
        "request": "How to I transition from a NFA to a DFA?",
        "date": "06.01.2024",
        "time": "11:17pm",
        "time-ago": "Yesterday",
        "price": 2.5,
        "method": "Text message",
        "user_id": 1,
    }

    questions = [
        question_one,
        question_two,
        question_three,
        question_four,
        question_five,
        question_six,
        question_seven,
        question_eight,
        question_nine,
    ]

    for q in questions:
        q["summary"] = (
            q["request"][0:127] + "..." if len(q["request"]) > 130 else q["request"]
        )
        q["solve-time"] = time_intervals[q["solve-time"]]["shortname"]
        q["user"] = users[q["user_id"]]["name"]
        q["major"] = users[q["user_id"]]["major"]
        q["year"] = users[q["user_id"]]["year"]

    return questions


def get_comments():
    comment_one = {
        "id": 1,
        "user": "Apple010",
        "message": "What is your preferred platform?",
        "reply_to": -1,
        "children": [],
    }

    comment_two = {
        "id": 2,
        "user": "OrangeJuice",
        "message": "Zoom is fine",
        "reply_to": 1,
        "children": [],
    }

    comment_three = {
        "id": 3,
        "user": "OrangeJuice",
        "message": "Actually, anything works.",
        "reply_to": 1,
        "children": [],
    }

    comment_four = {
        "id": 4,
        "user": "Apple010",
        "message": "Perfect!",
        "reply_to": 3,
        "children": [],
    }

    comment_five = {
        "id": 5,
        "user": "BigMonkey",
        "message": "Great Question!",
        "reply_to": -1,
        "children": [],
    }

    comments = [comment_one, comment_two, comment_three, comment_four, comment_five]

    users = [d["user"] for d in comments]

    for c in comments:
        c["user"] = f'User{users.index(c["user"])}'

    comments = sorted(comments, key=lambda d: d["id"], reverse=True)
    comments = sorted(comments, key=lambda d: d["reply_to"])

    for i in range(len(comments) - 1, -1, -1):
        c = comments[i]
        for j in range(i, -1, -1):
            if comments[j]["id"] == c["reply_to"]:
                comments[j]["children"].append(c)
                comments.pop()
                break

    comments = sorted(comments, key=lambda d: d["id"])

    return comments


def get_offers():

    offer_one = {
        "id": 1,
        "amount": 4.75,
        "major": "Computer Science",
        "year": "Junior",
        "comments": "None.",
        "status": "none",
        "user_id": 3,
    }

    offer_two = {
        "id": 2,
        "amount": 5.0,
        "major": "Information Science",
        "year": "Senior",
        "comments": "I prefer Zoom.",
        "status": "accepted",
        "user_id": 4,
    }

    offer_three = {
        "id": 3,
        "amount": 5.25,
        "major": "AEP",
        "year": "Sophomore",
        "comments": "Google meet",
        "status": "declined",
        "user_id": 5,
    }

    offers = [offer_one, offer_two, offer_three]

    for of in offers:
        of["user"] = users[of["user_id"]]["name"]
        of["major"] = users[of["user_id"]]["major"]
        of["year"] = users[of["user_id"]]["year"]
        of["rating"] = users[of["user_id"]]["rating"]

    return offers


def get_notifications():
    notification_one = {
        "id": 1,
        "message": "A user replied to your comment.",
        "link": "",
    }

    notification_two = {
        "id": 2,
        "message": "A user commented on your question.",
        "link": "",
    }

    notification_three = {
        "id": 3,
        "message": "A user made an offer to help you",
        "link": "",
    }

    notification_four = {
        "id": 4,
        "message": "Check this out!",
        "link": "",
    }

    notifications = [
        notification_one,
        notification_two,
        notification_three,
        notification_four,
    ]

    return notifications


@frontend.route("/")
def index():
    return render_template(
        "/home.html",
        subjects=subjects,
        methods=methods,
        time_intervals=time_intervals,
    )


@frontend.route("/login")
@no_token_allowed
def login():
    return render_template("signup.html", login=True)


@frontend.route("/signup")
@no_token_allowed
def signup():
    return render_template("signup.html", login=False, majors=majors)


@frontend.route("/dashboard")
def dashboard():
    questions = get_questions()

    notifications = get_notifications()

    return render_template(
        "dashboard.html",
        subjects=subjects,
        methods=methods,
        time_intervals=time_intervals,
        notifications=notifications,
        questions=questions,
    )


question = Blueprint("question", __name__, url_prefix="/question")


# Endpoint: /question/<id_itr>
@question.route("/<int:id_qstn>")
def fetch_question(id_qstn):
    notifications = get_notifications()

    questions = get_questions()

    question = None
    for qstn in questions:
        if qstn["id"] == id_qstn:
            question = qstn
            break

    if question is None:
        return "Question not found", 400

    comments = get_comments()

    made_offer = True

    accepted_offer = True
    if question["id"] % 3 == 0:
        accepted_offer = False

    is_author = False
    if question["id"] % 2 == 0:
        is_author = True

    offers = []
    if is_author:
        offers = get_offers()

    offer_made = None
    if made_offer:
        offer_made = get_offers()[0]

    offer_accepted = None
    if question["solved"]:
        offer_accepted = get_offers()[0]

    return render_template(
        "view.html",
        subjects=subjects,
        methods=methods,
        time_intervals=time_intervals,
        notifications=notifications,
        q=question,
        comments=comments,
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
