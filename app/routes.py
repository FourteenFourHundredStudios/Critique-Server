from flask import render_template
from flask import request
from flask import make_response,redirect
from app import app
from app import mongo
from flask import jsonify
from app import UserManager
from flask import send_from_directory
import json
from bson import ObjectId

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)



@app.route('/')
def index():
	return render_template("index.html")


@app.route('/static/<path:path>')
def send_js(path):
	return send_from_directory('static', path)


@app.route('/login', methods=['POST'])
def login():
	#print(request.data);
	loginVal=UserManager.login(request.json['username'],request.json['password'])
	if loginVal != None:
		#response = make_response(redirect('/home'))
		#response.set_cookie('sessionKey', str(loginVal))
		return jsonify({"status":"ok", "apiKey":str(loginVal)})
	else:
		return jsonify({"status":"error", "message":"invalid username or password!"})



@app.route('/getPosts', methods=['POST'])
@UserManager.validateUser
def getPosts(user):
	return JSONEncoder().encode(user.getPosts())

	
@app.route('/isMutual', methods=['POST'])
@UserManager.validateUser
def isMutual(user):
	return str(user.isMutual(request.json["user"]))

@app.route('/getFollows', methods=['POST'])
@UserManager.validateUser
def getFollows(user):
	return JSONEncoder().encode(user.getFollows())

@app.route('/getOldPosts', methods=['POST'])
@UserManager.validateUser
def getOldPosts(user):
	return JSONEncoder().encode(user.getOldPosts())

@app.route('/follow', methods=['POST'])
@UserManager.validateUser
def follow(user):
	return JSONEncoder().encode(user.follow(request.json["user"]))

@app.route('/sendPost', methods=['POST'])
@UserManager.validateUser
def sendPost(user):
	return JSONEncoder().encode(user.sendPost(request.json))

@app.route('/invalid')
def invalid():
	return "bad username or password"



@app.route('/home')
@UserManager.validateUser
def home(user):
	return "Hello, "+user.getUsername()



@app.route('/reset', methods=['POST'])
def rest():
	mongo.db.users.remove({})
	mongo.db.posts.remove({})
	mongo.db.users.insert({
		"username":"marc",
		"password":"nohash",
		"sessionKey":"1",
		"requiredPostIds":[],
		"following":["marc"]
	})
	
	mongo.db.posts.insert({"username":"marc","seen":[],"votes":{},"to":["marc","john"],"text":"test"})
	mongo.db.posts.insert({"username":"john","seen":[],"votes":{},"to":["john"],"text":"test"})
	mongo.db.posts.insert({"username":"john","seen":[],"votes":{},"to":["marc"],"text":"join the critique team"})
	mongo.db.posts.insert({"username":"ueee","seen":[],"votes":{},"to":["fast","marc"],"text":"test"})
	
	

	return "just doing stuff"