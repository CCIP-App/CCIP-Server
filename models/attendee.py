import bson
from models import db


class Scenario(db.EmbeddedDocument):
    order = db.IntField()
    available_time = db.IntField()
    expire_time = db.IntField()
    used = db.IntField()
    disabled = db.StringField()
    countdown = db.IntField()
    attr = db.DictField()


class Attendee(db.Document):
    token = db.StringField(unique=True)
    user_id = db.StringField()
    scenario = db.DictField()
    attr = db.DictField()

    meta = {
        'indexes': [
            'token'
        ]
    }

    def to_json(self):
        data = self.to_mongo()

        scenarios = []
        for k, v in data['scenario'].items():
            v.pop('_cls')
            v['id'] = k
            scenarios.append(v)

        data.pop('scenario')
        data['scenarios'] = sorted(scenarios, key=lambda k: k['order'])
        return bson.json_util.dumps(data)
