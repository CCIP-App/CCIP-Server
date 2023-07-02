from mongoengine import connect

import config

connect(**config.MONGODB_SETTINGS)

from models.attendee import *
from models.announcement import *
from models.puzzle import *
