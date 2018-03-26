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

	def follow(self,user):
		#DO CHECK TO MAKE SURE YOU CANT FOLLOW SAME USER TWICE
		mongo.db.posts.update({"username":self.getUsername()},{ 
			"$push": {"following":user}
		});
		return {"status":"ok"}


	def isMutual(self,user):
		return user in list(mongo.db.users.distinct("following",{"username":user})) or user==self.getUsername() or user=="self"
		
	def getFollows(self):
		return {
			"status":"ok",
			"message":list(mongo.db.users.distinct("following",{"username":self.getUsername()}))
		}

	def sendPost(self,params):
		#DO CHECKS FOR THIGS LIKE LENGTH AND VALID TYPE, ETC 
		for user in params["to"]:
			if not self.isMutual(user):
				return {"status":"error", "message":str(user)+" is not your mutual or does not exist!"}
		mongo.db.posts.insert({
			"username":self.getUsername(),
			"seen":[],
			"votes":{},
			"to":params["to"],
			"content":params["content"],
			"title":params["title"],
			"type":params["type"]
		})
		return {"status":"ok"}



	#potentially move to a celery task or something
	def castVotes(self,votes):

		ids=[]

		for vote in votes:
			ids.append(ObjectId(vote.get("id")))
			if vote["vote"]!=0 and vote["vote"]!=1:
				return {"status":"error","message":"Invalid vote IDs!"}

		#print(ids)
		#print(self.user["requiredPostIds"])

		if not set(ids).issubset( set(self.user["requiredPostIds"])):
			return {"status":"error","message":"Invalid vote IDs!"}


		mongo.db.users.update({ "username": self.getUsername()},{
			"$pull":{"requiredPostIds":{"$in":ids}}
		})




		for vote in votes:
			mongo.db.posts.update({ "_id": ObjectId(vote["id"])},{ 
				"$push": {"seen":self.getUsername()} ,
				"$set": {"votes."+self.getUsername(): vote["vote"] } } ,upsert=False)
			
		return {"status":"ok"}

			 

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

	def getOldPosts(self):
		find={
			"$and":[  
				{"to":{"$in": [self.getUsername()]}},  
				{"seen":{"$in": [self.getUsername()]}}  
			]
		}
		posts=mongo.db.posts.find(find).limit(15)

		return list(posts)

	def getPatchPath(self):
		return "../images/"+self.user["patch"]

	def setPatch(self,filename):
		#DO THING WHERE YOU DELETE OLD FILE FIRSTTT!!!!!!
		mongo.db.users.update({"username":self.getUsername()} , {"$set":{"patch":filename}})





	def getPosts(self):
		# split into several functions



		
		#in vote method make sure to check that the posts your validating were sent to you, AND you have not voted yet
		if len(self.user["requiredPostIds"]) > 3:
			
			"""
			#catch bson exception
			ids=[ObjectId(obj["id"]) for obj in self.request.json["votes"]]
 
			#print(self.user["requiredPostIds"])
			if ids != self.user["requiredPostIds"]:
			"""
			
			return {"status":"error", "message":"You have not voted on all past posts!"}

		"""
		if not self.castVotes(self.request.json["votes"]):
			return {"status":"error", "message":"Invalid vote! Vote must either be a 0 or 1"}
		"""


		find={
			"$and":[  
				{"to":{"$in": [self.getUsername()]}},  
				{"seen":{"$nin": [self.getUsername()]}}  
			]
		}
		update={"$push": {"seen":self.getUsername()} }	

		#amount of posts you can see at one time without voting on all prior posts is 5
		posts=mongo.db.posts.find(find).limit(5)
		
		postsValue=list(posts)
		
		
		
		posts.rewind()
		ids=[post.get("_id") for post in posts]
		
		#mongo.db.posts.update_many({ "_id": { "$in": ids } },update)
		
		mongo.db.users.update({"username":self.getUsername()} , {"$set":{"requiredPostIds":ids}})
		
		#remove votes so you can't see who voted for what until you've voted, and replace it w/ the number of votes
		for post in postsValue:
			post["votes"]=len(post["votes"])


		return {"status":"ok","message":postsValue}




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