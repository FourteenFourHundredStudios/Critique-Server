import pymongo

from app import mongo
import random
from functools import wraps
from flask import request
from flask import make_response, redirect
from flask import jsonify
from app import mutuals
from bson.objectid import ObjectId

from app.Lib.Reply import Reply
from app.Models.Model import Model
from app.Models.Post import Post


class User(Model):

	def __init__(self, username, password, session_key, patch, required_post_ids, score, following):
		super().__init__(-1)
		self.username = username
		self.password = password
		self.session_key = session_key
		self.patch = patch
		self.required_post_ids = required_post_ids
		self.score = score
		self.following = following

	def new_session(self):
		key = str(hash(random.randrange(100000, 5000000)))
		mongo.db.users.update_one({"username": self.username}, {
			'$set': {
				'sessionKey': key
			}
		})
		self.session_key = key
		print(self.session_key)

	def get_safe_user(self):
		return {
			"username": self.username,
			"sessionKey": self.session_key,
			"score": self.score,
			"following": self.following
		}

	def follow(self, user, following):
		# DO CHECK TO MAKE SURE USER EXISTS
		if following:
			if user not in self.following:
				mongo.db.users.update({"username": self.username}, {
					"$addToSet": {"following": user}
				});
				return Reply().ok()
			else:
				Reply().error("you are already following this user!")
		else:
			if user in self.following:
				mongo.db.users.update({"username": self.username}, {
					"$pull": {"following": user}
				});
				return Reply().ok()
			else:
				return Reply().error("you weren't following this user!")

	def is_mutual(self, user):
		return user in list(
			mongo.db.users.distinct("following", {"username": user})) or user == self.username or user == "self"

	def get_mutuals(self):
		query = mongo.db.users.find({"username": {"$in": self.following}})
		mutuals = User.create_from_db_obj(query)
		results = []
		for mutual in mutuals:
			user = {
				"username": mutual.username,
				"score": mutual.score,
				"isMutual": mutual.is_mutual(self.username)
			}
			results.append(user)
		return results

	def ids_required(self, ids):
		return set(ids).issubset(set(self.requiredPostIds))

	def cast_votes(self, votes):
		ids = []
		for vote in votes:
			ids.append(vote["id"])
			if vote["vote"] != 0 and vote["vote"] != 1:
				return Reply("Invalid vote IDs!").error()

		if not self.ids_required(ids):
			return Reply("Invalid vote IDs!").error("Invalid vote IDs!")

		mongo.db.users.update({"username": self.username}, {"$pull": {"requiredPostIds": {"$in": ids}}})

		posts = Post.create_from_db_ids(ids)
		for i, post in enumerate(posts):
			post.vote(self, votes[i]["id"])

		return Reply().ok()

	"""
		castVotes example API call:

		{
			"apiKey": "2230894",
			"votes" : [{"id":"5aa061abf7494320c0fd1497","vote":1}]
		}


		{
			"apiKey": "2230894",
			"votes" : [{"id":"5aa06733f749432182f4c363","vote":1},{"id":"5aa067daf7494321941d4952","vote":-1}]
		}
	"""

	# THIS FUNCTION IS BROKEN, FIX IT LATER
	def getOldPosts(self, page, count):
		find = {
			"$and": [
				{"to": {"$in": [self.getUsername()]}},
				{"$or": [

				]}
			]
		}

		up = {}
		down = {}
		up[self.getUsername()] = 1
		down[self.getUsername()] = 0

		find["$and"][1]["$or"].append({"votes": up})
		find["$and"][1]["$or"].append({"votes": down})

		posts = mongo.db.posts.find(find).sort([("_id", -1)]).skip(int(page) * 10).limit(10 * count)

		# posts=mongo.db.posts.find(find).sort([("_id",-1)]).skip(int(page)*10).limit(10)

		return list(posts)

	def getPatchPath(self):
		return "../images/" + self.user["patch"]

	def setPatch(self, filename):
		# DO THING WHERE YOU DELETE OLD FILE FIRSTTT!!!!!!
		mongo.db.users.update({"username": self.getUsername()}, {"$set": {"patch": filename}})

	def get_post(self, db_id):
		find = {
			"$and": [
				{"_id": ObjectId(db_id)},
				{"to": {"$in": [self.getUsername()]}},
				{"seen": {"$in": [self.getUsername()]}}
			]
		}
		results = mongo.db.posts.find(find)
		if results is not None:
			return Reply(Post.create_from_db_obj(results)).ok()
		else:
			return Reply("Could not find post with that Id!").error()

	def get_queue(self):
		if len(self.requiredPostIds) > 3:
			return Reply("You cannot have more than 3 un-voted posts!").error()
		find = {
			"$and": [
				{"to": {"$in": [self.username]}},
				{"seen": {"$nin": [self.username]}}
			]
		}
		posts = Post.create_from_db_obj(mongo.db.posts.find(find).limit(5))
		Post.mark_seen(self, posts)
		post_jsons = [post.get_safe_json() for post in posts]
		return Reply(post_jsons).ok()

	@staticmethod
	def get_from_username(username):
		user = mongo.db.users.find_one({"username": username})
		return User.create_from_db_obj(user)

	@staticmethod
	def create_from_db_obj(db_obj):
		if not isinstance(db_obj, pymongo.cursor.Cursor):
			user_obj = User(
				db_obj["username"],
				db_obj["password"],
				db_obj["sessionKey"],
				db_obj["patch"],
				db_obj["requiredPostIds"],
				db_obj["score"],
				db_obj["following"]
			)
			return user_obj
		else:
			users = list(db_obj)
			return [User.create_from_db_obj(user) for user in users]

	@staticmethod
	def login(username, password):
		user = mongo.db.users.find_one({"username": username, "password": password})
		if user is None:
			return None
		user = User.create_from_db_obj(user)
		user.new_session()
		return user.get_safe_user()

	@staticmethod
	def validate_user(api_method):
		@wraps(api_method)
		def check_api_key():
			if "debug" in request.json:
				user = mongo.db.users.find_one({"username": request.json["debug"]})
				user = User.create_from_db_obj(user)
				return api_method(user)
			elif "apiKey" in request.json:
				api_key = request.json["apiKey"]
				user = mongo.db.users.find_one({"sessionKey": api_key})
				if user is not None:
					user = User.create_from_db_obj(user)
					return api_method(user)
				else:
					return jsonify({"status": "error", "message": "Invalid apiKey!"})
			else:
				return jsonify({"status": "error", "message": "Invalid apiKey!"})
		return check_api_key
