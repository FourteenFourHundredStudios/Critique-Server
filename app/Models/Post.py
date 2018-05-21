import pymongo
from bson import ObjectId

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

	def send(self, requester):
		for user in self.to:
			if not requester.is_mutual(user):
				return Reply(str(user) + " is not your mutual or does not exist!").error()
		mongo.db.posts.insert({
			"username": self.username,
			"seen": self.seen,
			"votes": self.votes,
			"to": self.to,
			"content": self.content,
			"title": self.title,
			"type": self._type
		})
		return Reply().ok()

	def get_safe_json(self):
		return {
			"username": self.username,
			"seen": self.seen,
			"votes": len(self.votes),
			"to": self.to,
			"content": self.content,
			"title": self.title,
			"type": self._type
		}

	def vote(self, requester, vote):
		mongo.db.posts.update({"_id": self.db_id}, {
			"$set": {"votes." + requester.username: vote}}, upsert=False)

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
	def create_from_db_obj(db_obj):
		if not isinstance(db_obj, pymongo.cursor.Cursor):
			post_obj = Post(
				db_obj["_id"],
				db_obj["username"],
				db_obj["seen"],
				db_obj["votes"],
				db_obj["to"],
				db_obj["content"],
				db_obj["title"],
				db_obj["type"]
			)
			return post_obj
		else:
			posts = list(db_obj)
			return [Post.create_from_db_obj(post) for post in posts]

	@staticmethod
	def create_post(requester, to, content, title, type):
		return Post(requester, None, None, requester.username, to, content, title, type, {requester.username: 1})


