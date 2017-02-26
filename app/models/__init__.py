from flask_mongoengine import MongoEngine

db = MongoEngine()

from models.attendee import *
from models.announcement import *
from models.puzzle import *
