import pymongo
from datetime import datetime

import requests
from flask import json

from app import mongo
from app.Lib.Reply import Reply


from app.Models.Model import Model



class Post(Model):

	def __init__(self, db_id, username, to, content, title, type, seen, votes):
		super().__init__(db_id)
		self.username = username
		self.to = to
		self.content = content
		self.title = title
		self.type = type
		self.seen = seen
		self.votes = votes

	def notify(self, users, requester):
		from app.Models.User import User

		user_keys = [user.get_info("notificationKey") for user in User.get_from_username(users)]



		url = 'https://fcm.googleapis.com/fcm/send'
		key = 'AAAAxe-zm-c:APA91bFo5NK_jcUydvxbwbp1wWD3KCND2ul9xRLvZvi14aNjbAeQi6eJkbdU9wiFwawo7b6Af3rPuqoUH8q0vOfGYA40nRpIC436_SxBx2wbC1pl_CXTkA2Q_ev_yb-RUXQF66hS1YZq'
		body = {

			"registration_ids": user_keys,
			"priority": "high",
			"data": {
				"title": "Critique",
				"body": "from "+requester.username,
			}
		}
		headers = {
			"Content-Type": "application/json",
			"Authorization": "key="+key
		}
		r = requests.post(url, data=json.dumps(body), headers=headers)
		return Reply(str(r.reason)).ok()

	def send(self, requester, notify=True):
		for user in self.to:
			if not requester.is_mutual(user):
				return Reply(str(user) + " is not your mutual or does not exist!").error()
		post = {
			"username": self.username,
			"seen": self.seen,
			"votes": self.votes,
			"to": self.to,
			"content": self.content,
			"title": self.title,
			"type": self.type
		}
		mongo.db.posts.insert(post)
		if notify:
			self.notify(self.to, requester)

		return Reply().ok()

	def get_safe_json(self):
		return {
			"_id": self.db_id,
			"username": self.username,
			"seen": self.seen,
			"votes": len(self.votes),
			"to": self.to,
			"content": self.content,
			"title": self.title,
			"type": self.type
		}

	def vote(self, requester, vote):
		# consider creating vote Model?
		mongo.db.posts.update({"_id": self.db_id}, {
			"$push": {"votes": {
				"username": requester.username,
				"vote": vote,
				"date": datetime.utcnow()}
			}}, upsert=False)

	@staticmethod
	def mark_seen(requester, posts):
		ids = [post.db_id for post in posts]
		mongo.db.posts.update_many({"_id": {"$in": ids}}, {
			"$push": {"seen": requester.username},
		}, upsert=False)

	@staticmethod
	def create_from_db_ids(ids):
		results = mongo.db.posts.find({"_id": {"$in": ids}})
		return Post.create_from_db_obj(results)

	@staticmethod
	def get_ids(posts):
		return [post.db_id for post in posts]

	@staticmethod
	# db_id, username, to, content, title, type, seen, votes
	def create_from_db_obj(db_obj):
		if not isinstance(db_obj, pymongo.cursor.Cursor):
			post_obj = Post(
				db_obj["_id"],
				db_obj["username"],
				db_obj["to"],
				db_obj["content"],
				db_obj["title"],
				db_obj["type"],
				db_obj["seen"],
				db_obj["votes"]
			)
			return post_obj
		else:
			posts = list(db_obj)
			return [Post.create_from_db_obj(post) for post in posts]

	@staticmethod
	def create_post(requester, to, content, title, type="text"):
		return Post(-1, requester.username, to, content, title, type, [], [])


