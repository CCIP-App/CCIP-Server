import mongoengine as db


class Announcement(db.Document):
    datetime = db.IntField()
    msg_zh = db.StringField()
    msg_en = db.StringField()
    uri = db.StringField()
    role = db.ListField()
