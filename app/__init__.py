# app/__init__.py

from flask import Flask
from flask_pymongo import PyMongo

# Initialize the app
app = Flask(__name__, instance_relative_config=True)

app.config['MONGO_DBNAME'] = 'Critique'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/Critique'
app.config['TEMPLATES_AUTO_RELOAD'] = True

mongo = PyMongo(app)


# Load the views
from app import routes

# Load the config file
#app.config.from_object('config')