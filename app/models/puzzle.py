from models import db
from models import Attendee


class PuzzleStatus(db.Document):
    puzzle = db.StringField()
    quantity = db.IntField(default=0)
    currency = db.IntField(default=0)

    meta = {
        'indexes': [
            'puzzle'
        ]
    }


class PuzzleBucket(db.Document):
    attendee = db.ReferenceField(Attendee)
    public_token = db.StringField(unique=True)
    puzzle = db.ListField()
    valid = db.IntField()
    coupon = db.IntField()
    deliverer = db.ListField()

    meta = {
        'indexes': [
            'public_token'
        ]
    }
