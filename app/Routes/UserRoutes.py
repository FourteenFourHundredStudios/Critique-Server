from app import app, UserManager
from flask import request

from app.Lib.Reply import Reply
from app.Models import User
from app.Models.Post import Post


@app.route('/login', methods=['POST'])
def login():
	user = User.login(request.json['username'],request.json['password'])
	if user is not None:
		return Reply(user).ok()
	else:
		return Reply("Invalid username or password!").error()


@app.route('/castVotes', methods=['POST'])
@UserManager.validateUser
def cast_votes(user):
	return user.cast_votes(request.json["votes"])


@app.route('/getMutuals', methods=['POST'])
@User.validate_user
def get_mutuals(user):
	return Reply(user.get_mutuals).ok()


@app.route('/follow', methods=['POST'])
@User.validate_user
def follow(user):
	return user.follow(request.json["user"], request.json["following"])


@app.route('/sendPost', methods=['POST'])
@User.validate_user
def send_post(user):
	return Post.create_post(user, request.json["to"], request.json["title"], request.json["type"]).send(user)


@app.route('/getQueue', methods=['POST'])
@User.validate_user
def get_queue(user):
	return user.get_queue()


@app.route('/getPost', methods=['POST'])
@User.validate_user
def get_post(user):
	return
