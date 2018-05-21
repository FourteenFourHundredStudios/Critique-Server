# app/__init__.py

from flask import Flask
from flask_pymongo import PyMongo
from flask_uploads import UploadSet, configure_uploads, IMAGES

#pip install Flask-Uploads

# Initialize the app
app = Flask(__name__, instance_relative_config=True)

app.config['MONGO_DBNAME'] = 'Critique'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/Critique'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOADED_PHOTOS_DEST'] = 'images'


mongo = PyMongo(app)



from app import routes