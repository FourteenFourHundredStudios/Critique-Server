import pymongo
import bcrypt
import requests

from app import mongo
import random
from functools import wraps
from flask import request, json
from flask import make_response, redirect
from flask import jsonify
from bson.objectid import ObjectId

from app.Lib.Reply import Reply
from app.Models.Model import Model
from app.Models.Post import Post


class User(Model):

	def __init__(self, username, password, session_key, patch, required_post_ids, score, following, info):
		super().__init__(-1)
		self.username = username
		self.password = password
		self.session_key = session_key
		self.patch = patch
		self.required_post_ids = required_post_ids
		self.score = score
		self.following = following
		self.info = info

	def new_session(self):
		key = str(hash(random.randrange(100000, 5000000)))
		mongo.db.users.update_one({"username": self.username}, {
			'$set': {
				'sessionKey': key
			}
		})
		self.session_key = key


	""" 
	gets an overview requested by requester
	"""
	def get_overview(self, requester):
		return {
			"username": self.username,
			"isMutual": self.is_mutual(requester.username),
			"score": self.score
		}

	def get_safe_user(self, omit=[]):
		user = {
			"username": self.username,
			"sessionKey": self.session_key,
			"score": self.score,
			"following": self.get_mutuals()
		}

		if len(omit) is not []:
			for element in omit:
				del user[element]

		return user

	def add_info(self, key, value):
		mongo.db.users.update({"username": self.username}, {
			"$set": {"info."+key: value}
		});

	def get_info(self, key):
		return self.info[key]

	def follow(self, user, following):
		# DO CHECK TO MAKE SURE USER EXISTS
		if following:
			if user not in self.following:
				mongo.db.users.update({"username": self.username}, {
					"$addToSet": {"following": user}
				});
				return Reply().ok()
			else:
				return Reply("you are already following this user!").error()
		else:
			if user in self.following:
				mongo.db.users.update({"username": self.username}, {
					"$pull": {"following": user}
				});
				return Reply().ok()
			else:
				return Reply("you weren't following this user!").error()

	def is_mutual(self, user):
		return user in self.following

	def send_post_notification(self, user):
		url = 'https://fcm.googleapis.com/fcm/send'
		key = 'AAAAxe-zm-c:APA91bFo5NK_jcUydvxbwbp1wWD3KCND2ul9xRLvZvi14aNjbAeQi6eJkbdU9wiFwawo7b6Af3rPuqoUH8q0vOfGYA40nRpIC436_SxBx2wbC1pl_CXTkA2Q_ev_yb-RUXQF66hS1YZq'
		body = {

			"registration_ids": [self.get_info("notificationKey")],
			"priority": "high",
			"data": {
				"title": "Critique",
				"body": "from "+user.username,

			}
		}
		headers = {
			"Content-Type": "application/json",
			"Authorization": "key="+key
		}
		r = requests.post(url, data=json.dumps(body), headers=headers)
		return Reply(str(r.reason)).ok()

	def get_mutuals(self):
		results = [mutual.get_overview(self) for mutual in User.get_from_username(self.following)]
		return results

	def ids_required(self, ids):
		return set(ids).issubset(set(self.required_post_ids))

	def cast_votes(self, votes):
		ids = []
		print(votes)
		for vote in votes:
			ids.append(ObjectId(vote["id"]))
			if vote["vote"] != 0 and vote["vote"] != 1:
				return Reply("Invalid vote IDs!").error()

		if not self.ids_required(ids):
			return Reply("Invalid vote IDs!").error()

		mongo.db.users.update({"username": self.username}, {"$pull": {"requiredPostIds": {"$in": ids}}})

		posts = Post.create_from_db_ids(ids)
		for i, post in enumerate(posts):
			post.vote(self, votes[i]["vote"])
		return Reply().ok()

	def get_archive(self, page, count):
		find = {
			"$and": [
				{"to": {"$in": [self.username]}},
				{"seen": {"$in": [self.username]}},
				{"votes": {"$elemMatch": {"username": self.username}}},
			]
		}
		posts = mongo.db.posts.find(find).sort([("_id", -1)]).skip(int(page) * 10).limit(10 * count)
		return list(posts)



	def get_patch_path(self):
		return "../images/" + self.patch

	def set_patch(self, filename):
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
		if len(self.required_post_ids) > 3:
			return Reply("You cannot have more than 3 un-voted posts!").error()
		find = {
			"$and": [
				{"to": {"$in": [self.username]}},
				{"seen": {"$nin": [self.username]}}
			]
		}
		posts = Post.create_from_db_obj(mongo.db.posts.find(find).limit(5))
		Post.mark_seen(self, posts)
		mongo.db.users.update({"username": self.username}, {"$push": {"requiredPostIds": {"$each": Post.get_ids(posts)}}})
		post_jsons = [post.get_safe_json() for post in posts]

		return Reply(post_jsons).ok()

	@staticmethod
	def create_new_user(username, password, validating=True, patch="default.png", required_post_ids=[], score=0, following=[], info={}):

		if validating:
			if len(username) < 6:
				return Reply("Your username must be at least 6 characters!").error()
			elif len(password) < 6:
				return Reply("Your password must be at least 6 characters!").error()
		try:
			salt = bcrypt.gensalt()
			following.append(username)

			#print(bcrypt.hashpw(password.encode(), salt))

			mongo.db.users.insert({
				"username": username,
				"password": bcrypt.hashpw(password.encode(), salt),
				"patch": patch,
				"sessionKey": None,
				"requiredPostIds": required_post_ids,
				"score": score,
				"following": following,
				"info": info
			})
		except pymongo.errors.PyMongoError as e:
			print(e)
			return Reply("This username is already taken!").error()
		return Reply().ok()

	@staticmethod
	def get_from_username(username):
		if isinstance(username, list):
			user = mongo.db.users.find({"username": {"$in": username}})
		else:
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
				db_obj["following"],
				db_obj["info"]
			)
			return user_obj
		else:
			users = list(db_obj)
			return [User.create_from_db_obj(user) for user in users]

	@staticmethod
	def login(username, password):
		user = mongo.db.users.find_one({"username": username})
		if user is not None:
			hash = bcrypt.hashpw(password.encode(), user["password"])
			if not (str(hash) == str(user["password"])):
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
					return Reply("Invalid apiKey!").error()
			else:
				return Reply("Invalid apiKey!").error()
		return check_api_key
