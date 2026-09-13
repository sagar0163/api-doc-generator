"""Fixture Flask app used to smoke-test `apidocgen generate`."""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello, world!"


@app.route("/users", methods=["GET"])
def list_users():
    return "[]"


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return "{}"