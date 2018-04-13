from app import mongo
import random 
from functools import wraps
from flask import request
from flask import make_response,redirect
from flask import jsonify
from app import mutuals
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
		#print(user)
		mongo.db.users.update({"username":self.getUsername()},{ 
			"$push": {"following":user}
		});
		return {"status":"ok"}


	def isMutual(self,user):
		return user in list(mongo.db.users.distinct("following",{"username":user})) or user==self.getUsername() or user=="self"
		
	def getMutuals(self):
		return list(mongo.db.users.aggregate(mutuals.getMutuals(self.getUsername())))
		

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




		"""
		for vote in votes:
			mongo.db.posts.update({ "_id": ObjectId(vote["id"])},{ 
				"$push": {"seen":self.getUsername()} ,
				"$set": {"votes."+self.getUsername(): vote["vote"] } } ,upsert=False)
		"""	

		#change to update_many later
		for vote in votes:
			mongo.db.posts.update({ "_id": ObjectId(vote["id"])},{ 
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

	#THIS FUNCTION IS BROKEN, FIX IT LATER
	def getOldPosts(self,page,count):
		find={
			"$and":[  
				{"to":{"$in": [self.getUsername()]}},  
				{"$or":[
					
				]}
			]
		}

		up={}
		down={}
		up[self.getUsername()]=1
		down[self.getUsername()]=0

		find["$and"][1]["$or"].append({"votes":up})
		find["$and"][1]["$or"].append({"votes":down})


		posts=mongo.db.posts.find(find).sort([("_id",-1)]).skip(int(page)*10).limit(10*count)

		#posts=mongo.db.posts.find(find).sort([("_id",-1)]).skip(int(page)*10).limit(10)

		


		return list(posts)

	def getPatchPath(self):
		return "../images/"+self.user["patch"]

	def setPatch(self,filename):
		#DO THING WHERE YOU DELETE OLD FILE FIRSTTT!!!!!!
		mongo.db.users.update({"username":self.getUsername()} , {"$set":{"patch":filename}})


	def getPost(self,id):
		find={
			"$and":[  
				{"_id":ObjectId(id)},
				{"to":{"$in": [self.getUsername()]}}, 
				{"seen":{"$in": [self.getUsername()]}}  
			]
		}
		return list(mongo.db.posts.find_one(find))

	def getPosts(self):
		# split into several functions



		
		#in vote method make sure to check that the posts your validating were sent to you, AND you have not voted yet
		#print(self.user["requiredPostIds"])
		
		
	
		if len(self.user["requiredPostIds"]) > 3:

			return {"status":"error", "message":"You cannot have more than 1 unvoted post!"}
	



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
		

		mongo.db.posts.update_many({ "_id": { "$in": ids } },{ 
			"$push": {"seen":self.getUsername()} ,
		} ,upsert=False)

		#mongo.db.posts.update_many({ "_id": { "$in": ids } },update)
		
		mongo.db.users.update({"username":self.getUsername()} , {"$push": {"requiredPostIds":{ "$each": ids }}})
		
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
		if "debug" in request.json:
			u=mongo.db.users.find_one({"username":request.json["debug"]})
			user = User(u["sessionKey"],request)
			return api_method(user)
		elif "apiKey" in request.json:
			apiKey = request.json["apiKey"]
			user = User(apiKey,request)

			if user.isValid():
				return api_method(user)
			else:
				return jsonify({"status":"error", "message":"Invalid apiKey!"})
		else:
			return jsonify({"status":"error", "message":"Invalid apiKey!"})
	return check_api_key