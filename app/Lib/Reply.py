from bson import ObjectId
from flask import json


class JSONEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, ObjectId):
			return str(o)

		return json.JSONEncoder.default(self, o)


class Reply (object):

	def __init__(self, message):
		self.message = message

	def ok_message(self):
		result = {
			"status": "ok",
			"message": self.message
		}
		return JSONEncoder().encode(result)

	def ok(self):
		result = {
			"status": "ok",
		}
		return JSONEncoder().encode(result)

	def error(self):
		result = {
			"status": "error",
			"message": self.message
		}
		return JSONEncoder().encode(result)