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
import base64
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask import send_file

#self IS A RESTRICTED USERNAME THAT REFERES TO yourself

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)



@app.route('/')
def index():
	return render_template("index.html")

@app.route('/search/<username>', methods=['GET','POST'])
def doSearch(username):
	users=list(mongo.db.users.find({"username":{"$regex": username}}))
	return jsonify({"results":[user["username"] for user in users]})



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

@app.route('/getPatch/<apiKey>/<username>', methods=["GET",'POST'])
def getPatch(apiKey,username):
	user = UserManager.User(apiKey,{})
	if(user.isMutual(username)):
		path = "error.png"
		if username!="self":
			path = mongo.db.users.find_one({"username":username})["patch"]
		else:
			path=user.getPatchPath()
		return send_file("../images/"+path, mimetype='image/png')
	else:
		return jsonify({"status":"error","message":"This user is not your mutual!"})

#move form params to url strings
@app.route('/setPatch', methods=['POST'])
def setPatch():
	user = UserManager.User(request.form["apiKey"],request.form)
	photos = UploadSet('photos', IMAGES)
	if request.method == 'POST' and 'pic' in request.files:
		configure_uploads(app, photos)
		filename = photos.save(request.files['pic'])
		user.setPatch(filename)
		return jsonify({"status":"ok"})
	else:
		return jsonify({"status":"error","message":"could not save image!"})


@app.route('/getPosts', methods=['POST'])
@UserManager.validateUser
def getPosts(user):
	return JSONEncoder().encode(user.getPosts())

@app.route('/castVotes', methods=['POST'])
@UserManager.validateUser
def castVotes(user):
	return JSONEncoder().encode(user.castVotes(request.json["votes"]))

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
		"patch":"default.png",
		"requiredPostIds":[],
		"following":["marc","john","adam","test","snakes"]
	})
	
	mongo.db.users.insert({
		"username":"adam",
		"password":"nohash",
		"sessionKey":"2",
		"patch":"default.png",
		"requiredPostIds":[],
		"following":["marc","john","adam","test","snakes"]
	})

	mongo.db.users.insert({
		"username":"noah",
		"password":"nohash",
		"sessionKey":"3",
		"patch":"default.png",
		"requiredPostIds":[],
		"following":["marc","john","adam","test","snakes"]
	})

	#mongo.db.posts.insert({"username":"marc","title":"Real Post!","type":"text","seen":[],"votes":{},"to":["marc","john"],"content":"This is the first Critique post that has ever been rendered from the server! Whoa!!"})
	#mongo.db.posts.insert({"username":"marc","title":"Nooo","type":"text","seen":[],"votes":{},"to":["john"],"content":"NOPE!"})
	
	for i in range(37):
		mongo.db.posts.insert({"username":"marc","title":"Test post "+str(i),"type":"text","seen":[],"votes":{},"to":["marc","john"],"content":"see 2"})
	

	return "just doing stuff"