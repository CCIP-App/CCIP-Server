from models import db


class PuzzleStatus(db.Document):
    puzzle = db.DictField()
