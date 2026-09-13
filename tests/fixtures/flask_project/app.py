from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return jsonify({"user_id": user_id})

@app.route("/users/", methods=["POST"])
def create_user():
    return jsonify({"status": "created"}), 201
    
@app.route("/missing", methods=["GET"])
def missing():
    return jsonify({"error": "Not found"}), 404
