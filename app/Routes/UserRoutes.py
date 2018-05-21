from app import app, UserManager
from flask import request

from app.Models import User


@app.route('/login', methods=['POST'])
def login():
	user = User.login(request.json['username'],request.json['password'])
	if user is not None:
		return jsonify(user)
	else:
		return jsonify({"status":"error", "message":"invalid username or password!"})


@app.route('/castVotes', methods=['POST'])
@UserManager.validateUser
def cast_votes(user):
	return user.cast_votes(request.json["votes"])