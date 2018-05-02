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
	return jsonify({"results":[{"username":user["username"],"score":user["score"]} for user in users]})



@app.route('/static/<path:path>')
def send_js(path):
	return send_from_directory('static', path)


@app.route('/login', methods=['POST'])
def login():
	#print(request.data);
	user=UserManager.login(request.json['username'],request.json['password'])
	if user != None:
		#response = make_response(redirect('/home'))
		#response.set_cookie('sessionKey', str(loginVal))
		return jsonify({"status":"ok", "apiKey":str(user.getAttribute("sessionKey")),"score":str(user.getAttribute("score")),"mutuals":user.getMutuals()})
	else:
		return jsonify({"status":"error", "message":"invalid username or password!"})

@app.route('/getPatch/<apiKey>/<username>', methods=["GET",'POST'])
def getPatch(apiKey,username):
	user = UserManager.User(apiKey,{})
	#if(user.isMutual(username)):
	path = "error.png"
	if username!="self":
		path = mongo.db.users.find_one({"username":username})["patch"]
	else:
		path=user.getPatchPath()
	return send_file("../images/"+path, mimetype='image/png')
	#else:
		#return jsonify({"status":"error","message":"This user is not your mutual!"})




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
	#print (user.getUsername())
	return JSONEncoder().encode(user.getPosts())


@app.route('/castVotes', methods=['POST'])
@UserManager.validateUser
def castVotes(user):
	return JSONEncoder().encode(user.castVotes(request.json["votes"]))

@app.route('/isMutual', methods=['POST'])
@UserManager.validateUser
def isMutual(user):
	return JSONEncoder().encode(user.isMutual(request.json["user"]))

@app.route('/getMutuals', methods=['POST'])
@UserManager.validateUser
def getFollows(user):
	res={
		"mutuals":user.getMutuals(),
		"status":"ok"
	}
	return JSONEncoder().encode(res)

@app.route('/getArchive', methods=['POST'])
@UserManager.validateUser
def getArchive(user):
	return JSONEncoder().encode({"archive":user.getOldPosts(request.json["page"],request.json["count"])})


@app.route('/getPost', methods=['POST'])
@UserManager.validateUser
def getPost(user):
	return JSONEncoder().encode(user.getPost(request.json["id"]))

@app.route('/follow', methods=['POST'])
@UserManager.validateUser
def follow(user):
	return JSONEncoder().encode(user.follow(request.json["user"]))


@app.route('/unfollow', methods=['POST'])
@UserManager.validateUser
def unfollow(user):
	return JSONEncoder().encode(user.unfollow(request.json["user"]))

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
		"score":1000,
		"following":["john","noah","marc"]
	})
	
	mongo.db.users.insert({
		"username":"john",
		"password":"nohash",
		"sessionKey":"2",
		"patch":"1522471380034.png",
		"requiredPostIds":[],
		"score":2342,
		"following":["marc","john","adam"]
	})

	mongo.db.users.insert({
		"username":"adam",
		"password":"nohash",
		"sessionKey":"6789098765678",
		"patch":"1523740911313.png",
		"requiredPostIds":[],
		"score":-1000,
		"following":["adam"]
	})


	mongo.db.users.insert({
		"username":"noah",
		"password":"nohash",
		"sessionKey":"3",
		"patch":"1523135328801.png",
		"requiredPostIds":[],
		"score":3333,
		"following":["marc","john","adam","test","snakes"]
	})

	mongo.db.users.insert({
		"username":"aCritqueGuy",
		"password":"nohash",
		"sessionKey":"32r3efw",
		"patch":"1523395202020.png",
		"requiredPostIds":[],
		"score":45432,
		"following":[]
	})

	#mongo.db.posts.insert({"username":"marc","title":"Real Post!","type":"text","seen":[],"votes":{},"to":["marc","john"],"content":"This is the first Critique post that has ever been rendered from the server! Whoa!!"})
	#mongo.db.posts.insert({"username":"marc","title":"Nooo","type":"text","seen":[],"votes":{},"to":["john"],"content":"NOPE!"})
	

	for i in range(5):
		mongo.db.posts.insert({"username":"marc","title":"Test post "+str(i),"type":"text","seen":[],"votes":{},"to":["marc","john"],"content":"http://google.com/"})

	mongo.db.posts.insert({"username":"marc","title":"one","type":"text","seen":[],"votes":{},"to":["marc","john"],"content":"http://google.com/"})


	return JSONEncoder().encode({"status":"nuked"})

@app.route('/postTest', methods=['POST'])
def fwofkweo():
	for i in range(25):
		#mongo.db.posts.insert({"username":"john","title":"Test post "+str(i),"type":"text","seen":[],"votes":{},"to":["marc"],"content":"This is a fake post that has been generated by the Critique server!"})
		mongo.db.posts.insert({"username":"marc","title":"Test post "+str(i),"type":"text","seen":[],"votes":{},"to":["marc","john"],"content":"http://graphql.org/"})
		mongo.db.posts.insert({"username":"john","title":"Test post "+str(i),"type":"text","seen":[],"votes":{},"to":["marc","john"],"content":"This is a fake post that has been generated by the Critique server!"})
	return "just doing stuff2"