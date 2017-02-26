from models import db
from models import Attendee


class PuzzleStatus(db.Document):
    puzzle = db.DictField()


class PuzzleBucket(db.Document):
    attendee = db.ReferenceField(Attendee)
    public_token = db.StringField()
    puzzle = db.ListField()

    meta = {
        'indexes': [
            'public_token'
        ]
    }
