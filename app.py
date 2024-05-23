from flask import Flask, render_template, request
import time

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("landing.html")


@app.route("/dash", methods=["POST", "GET"])
def dashboard():
    return render_template("dashboard2.html")


@app.route("/view", methods=["POST", "GET"])
def view():
    return render_template("view.html")
