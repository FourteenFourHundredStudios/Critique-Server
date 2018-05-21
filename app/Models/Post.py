from bson import ObjectId

from app import mongo
from app.Models.Model import Model


class Post(Model):

	def __init__(self, requester, db_id, username, to, content, title, type, seen, votes):
		super().__init__(db_id)
		self._requester = requester
		self._username = username
		self._to = to
		self._content = content
		self._title = title
		self._type = type
		self._seen = seen
		self._votes = votes

	def send(self):
		for user in self.to:
			if not self.requester.is_mutual(user):
				return {"status": "error", "message": str(user) + " is not your mutual or does not exist!"}
		mongo.db.posts.insert({
			"username": self.username,
			"seen": self.seen,
			"votes": self.votes,
			"to": self.to,
			"content": self.content,
			"title": self.title,
			"type": self._type
		})
		return {"status": "error", "message": str(user) + " is not your mutual or does not exist!"}

	def vote(self, vote):
		mongo.db.posts.update({"_id": self.db_id}, {
			"$set": {"votes." + self.requester.username: vote}}, upsert=False)

	@staticmethod
	def get_from_id(requester, db_id):
		return Post(requester, db_id, None, None, None, None, None, None, None)

	@staticmethod
	def create_post(requester, to, content, title, type):
		return Post(requester, None, None, requester.username, to, content, title, type, {requester.username: 1})


