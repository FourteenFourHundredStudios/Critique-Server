from app import app, mongo
from app.Lib.Reply import Reply
from app.Models.User import User
from app.Models.Post import Post


@app.route('/debug/reset/hard', methods=['POST'])
def hard_reset():
	mongo.db.users.remove({})
	mongo.db.posts.remove({})
	User.create_new_user("marc", "nohash", validating=False, following=["adam", "john"])
	User.create_new_user("adam", "password", validating=False, patch="adam.png", following=["marc", "noah"])
	User.create_new_user("john", "password", validating=False, patch="john.png", following=["adam", "critique"])
	User.create_new_user("critique", "critique", validating=False, patch="critique.png", following=["adam", "john", "marc","noah"])
	return Reply().ok()


@app.route('/debug/reset', methods=['POST'])
def reset():
	mongo.db.users.update({}, {"$set": {"requiredPostIds": [] } }, upsert=True)
	mongo.db.posts.remove({})
	return Reply().ok()


@app.route('/debug/posts/<username>', methods=['POST'])
def posts(username):
	mongo.db.posts.remove({})
	user = User.get_from_username("adam")
	for i in range(15):
		post = Post.create_post(user, [username], "This is a Critique post!", "Test post "+str(i))
		print(post.send(user))
	return Reply().ok()
