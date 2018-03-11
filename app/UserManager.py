from app import mongo
import random 
from functools import wraps
from flask import request
from flask import make_response,redirect
from flask import jsonify
from bson.objectid import ObjectId

class User(object):
	sessionKey=None
	request=None
	user={}
	

	def __init__(self,sessionKey,request):
		self.sessionKey=sessionKey
		self.request=request
		self.user=mongo.db.users.find_one({"sessionKey":sessionKey})
	
	def getAttribute(self,attr):
		return self.user[attr]

	def getUsername(self):
		return self.user["username"]

	def isValid(self):
		return self.user != None


	#potentially move to a celery task or something
	def castVotes(self,votes):
		

		#this seems stupid, but you cant only update some of the posts if it fails
		for vote in votes:
			
			if vote["vote"]!=0 and vote["vote"]!=1:
				return False

		for vote in votes:


			mongo.db.posts.update({ "_id": ObjectId(vote["id"])},{ 
				"$push": {"seen":self.getUsername()} ,
				"$set": {"votes."+self.getUsername(): vote["vote"] } } ,upsert=False)
		return True
			 

	"""
	 	getPosts example API call:

		{
			"apiKey": "2230894",
			"votes" : [{"id":"5aa061abf7494320c0fd1497","vote":1}]
		}


		{
			"apiKey": "2230894",
			"votes" : [{"id":"5aa06733f749432182f4c363","vote":1},{"id":"5aa067daf7494321941d4952","vote":-1}]
		}
	"""

	def getOldPosts(self):
		find={
			"$and":[  
				{"to":{"$in": [self.getUsername()]}},  
				{"seen":{"$in": [self.getUsername()]}}  
			]
		}
		posts=mongo.db.posts.find(find).limit(15)

		return list(posts)



	def getPosts(self):
		# split into several functions

		#in vote method make sure to check that the posts your validating were sent to you, AND you have not voted yet
		if len(self.user["requiredPostIds"]) != 0:
			
			#catch bson exception
			ids=[ObjectId(obj["id"]) for obj in self.request.json["votes"]]
 
			#print(self.user["requiredPostIds"])
			if ids != self.user["requiredPostIds"]:
				return {"status":"error", "message":"Invalid vote IDs!"}

		if not self.castVotes(self.request.json["votes"]):
			return {"status":"error", "message":"Invalid vote! Vote must either be a 0 or 1"}

		find={
			"$and":[  
				{"to":{"$in": [self.getUsername()]}},  
				{"seen":{"$nin": [self.getUsername()]}}  
			]
		}
		update={"$push": {"seen":self.getUsername()} }	

		#amount of posts you can see at one time without voting is 5
		posts=mongo.db.posts.find(find).limit(5)
		
		postsValue=list(posts)
		
		
		
		posts.rewind()
		ids=[post.get("_id") for post in posts]
		
		#mongo.db.posts.update_many({ "_id": { "$in": ids } },update)
		
		mongo.db.users.update({"username":self.getUsername()} , {"$set":{"requiredPostIds":ids}})
		
		#remove votes so you can't see who voted for what until you've voted
		for post in postsValue:
			post["votes"]="Hidden"

		return postsValue




def login(username,password):
	user=mongo.db.users.find_one({"username":username,"password":password})
	if user == None:
		return None
	else:
		key=str(hash(random.randrange(100000,5000000)))
		mongo.db.users.update_one({"username":user["username"]},{
			'$set': {
				'sessionKey':key
			}
		})
		return key
	return user





def validateUser(api_method):
	@wraps(api_method)
	def check_api_key():
		"""
		if 'sessionKey' in request.cookies:
			sessionKey = request.cookies["sessionKey"]
			user = User(sessionKey)
			if user.isValid():
				return api_method(user)
			else:
				return "You must login to view this page!"
		else:
			return "You must login to view this page!"
		"""

		if "apiKey" in request.json:
			apiKey = request.json["apiKey"]
			user = User(apiKey,request)

			if user.isValid():
				return api_method(user)
			else:
				return jsonify({"status":"error", "message":"Invalid apiKey!"})
		else:
			return jsonify({"status":"error", "message":"Invalid apiKey!"})
	return check_api_key