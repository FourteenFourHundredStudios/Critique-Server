from bson import ObjectId
from flask import json


class JSONEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, ObjectId):
			return str(o)

		return json.JSONEncoder.default(self, o)


class Reply (object):

	def __init__(self, message=None):
		self.message = message

	def ok(self):
		result = {
			"status": "ok"
		}
		if self.message is not None:
			result["response"] = self.message
		return JSONEncoder().encode(result)

	def error(self):
		result = {
			"status": "error",
			"response": self.message
		}
		return JSONEncoder().encode(result)