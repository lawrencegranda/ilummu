from flask import Flask, render_template, request, Blueprint
import time

app = Flask(__name__)


def get_questions():
    question_one = {
        "id": 1,
        "solved": False,
        "subject": "Business",
        "number": "AEM 2200",
        "name": "Business Man and Org",
        "solve-time": 25,
        "request": "How do I create a SWOT analysis?",
        "date": "06.02.2024",
        "time": "5:28pm",
        "time-ago": "2 min ago",
        "price": 5,
        "method": "Video call",
        "user": "OrangeJuice",
    }

    question_two = {
        "id": 2,
        "solved": False,
        "subject": "Mathematics",
        "number": "MATH 2940",
        "name": "Linear Algebra for Engineers",
        "solve-time": 45,
        "request": "Explain SVD to me",
        "date": "05.31.2024",
        "time": "6:00pm",
        "time-ago": "Two days ago",
        "price": 4.25,
        "method": "Voice call",
        "user": "OrangeJuice",
    }

    question_three = {
        "id": 3,
        "solved": True,
        "subject": "Computer Science",
        "number": "CS 2800",
        "name": "Discrete Math",
        "solve-time": 10,
        "request": "How to I transition from a NFA to a DFA?",
        "date": "06.01.2024",
        "time": "11:17pm",
        "time-ago": "Yesterday",
        "price": 2.5,
        "method": "Text message",
        "user": "OrangeJuice",
    }

    question_four = {
        "id": 4,
        "solved": True,
        "subject": "Computer Science",
        "number": "CS 3110",
        "name": "Functional Programming",
        "solve-time": 7,
        "request": "How do I curry a function?",
        "date": "05.26.2024",
        "time": "7:47am",
        "time-ago": "A week ago",
        "price": 2,
        "method": "Text message",
        "user": "OrangeJuice",
    }

    return [question_one, question_two, question_three, question_four]


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

    print(comments)
    return comments


def get_offers():

    offer_one = {
        "id": 1,
        "amount": 4.75,
        "major": "Computer Science",
        "year": "Junior",
        "comments": "None.",
    }

    offer_two = {
        "id": 2,
        "amount": 5.0,
        "major": "Information Science",
        "year": "Senior",
        "comments": "I prefer Zoom.",
    }

    offers = [offer_one, offer_two]

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


@app.route("/")
def index():
    return render_template("landing.html")


@app.route("/dashboard", methods=["POST", "GET"])
def dashboard():
    questions = get_questions()

    notifications = get_notifications()

    return render_template(
        "dashboard.html", notifications=notifications, questions=questions
    )


@app.route("/view", methods=["POST", "GET"])
def view():
    notifications = get_notifications()

    question = get_questions()[1]
    comments = get_comments()

    is_author = False
    offers = []
    if is_author:
        offers = get_offers()

    return render_template(
        "view.html",
        notifications=notifications,
        q=question,
        comments=comments,
        is_author=is_author,
        offers=offers,
    )


question = Blueprint("question", __name__, url_prefix="/question")


# Endpoint: /question/<id_itr>
@question.route("/<int:id_qstn>", methods=["POST", "GET"])
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

    is_author = True
    offers = []
    if is_author:
        offers = get_offers()

    return render_template(
        "view.html",
        notifications=notifications,
        q=question,
        comments=comments,
        is_author=is_author,
        offers=offers,
    )


app.register_blueprint(question)
