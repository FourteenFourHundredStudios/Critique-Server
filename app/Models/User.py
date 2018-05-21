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
			if not user in self.following:
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

		return Reply("ok",results)


	def send_post(self, params):
		post = Post.create_post(self,params["to"],params["content"],params["title"],params["type"])
		return post.send()

	# potentially move to a celery task or something
	def castVotes(self, votes):

		ids = []

		for vote in votes:
			ids.append(ObjectId(vote.get("id")))
			if vote["vote"] != 0 and vote["vote"] != 1:
				return {"status": "error", "message": "Invalid vote IDs!"}

		if not set(ids).issubset(set(self.user["requiredPostIds"])):
			return {"status": "error", "message": "Invalid vote IDs!"}

		mongo.db.users.update({"username": self.getUsername()}, {
			"$pull": {"requiredPostIds": {"$in": ids}}
		})

		"""
		for vote in votes:
			mongo.db.posts.update({ "_id": ObjectId(vote["id"])},{ 
				"$push": {"seen":self.getUsername()} ,
				"$set": {"votes."+self.getUsername(): vote["vote"] } } ,upsert=False)
		"""

		# change to update_many later
		for vote in votes:
			mongo.db.posts.update({"_id": ObjectId(vote["id"])}, {
				"$set": {"votes." + self.getUsername(): vote["vote"]}}, upsert=False)

		return {"status": "ok"}

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

	def getPost(self, id):
		find = {
			"$and": [
				{"_id": ObjectId(id)},
				{"to": {"$in": [self.getUsername()]}},
				{"seen": {"$in": [self.getUsername()]}}
			]
		}
		return list(mongo.db.posts.find_one(find))

	def getPosts(self):
		# split into several functions

		# in vote method make sure to check that the posts your validating were sent to you, AND you have not voted yet
		# print(self.user["requiredPostIds"])

		if len(self.user["requiredPostIds"]) > 3:
			return {"status": "error", "message": "You cannot have more than 1 unvoted post!"}

		find = {
			"$and": [
				{"to": {"$in": [self.getUsername()]}},
				{"seen": {"$nin": [self.getUsername()]}}
			]
		}
		update = {"$push": {"seen": self.getUsername()}}

		# amount of posts you can see at one time without voting on all prior posts is 5
		posts = mongo.db.posts.find(find).limit(5)

		postsValue = list(posts)

		posts.rewind()
		ids = [post.get("_id") for post in posts]

		mongo.db.posts.update_many({"_id": {"$in": ids}}, {
			"$push": {"seen": self.getUsername()},
		}, upsert=False)

		# mongo.db.posts.update_many({ "_id": { "$in": ids } },update)

		mongo.db.users.update({"username": self.getUsername()}, {"$push": {"requiredPostIds": {"$each": ids}}})

		# remove votes so you can't see who voted for what until you've voted, and replace it w/ the number of votes
		for post in postsValue:
			post["votes"] = len(post["votes"])

		return {"status": "ok", "message": postsValue}

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
