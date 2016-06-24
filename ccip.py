import bson
import time
from error import Error
from flask import Flask, request, jsonify
from flask_mongoengine import MongoEngine
from mongoengine.queryset import DoesNotExist

db = MongoEngine()

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)


class Scenario(db.EmbeddedDocument):
    order = db.IntField()
    available_time = db.IntField()
    expire_time = db.IntField()
    used = db.IntField()
    disabled = db.StringField()
    attr = db.DictField()


class Attendee(db.Document):
    token = db.StringField(unique=True)
    user_id = db.StringField()
    scenario = db.DictField()

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


def get_attendee(request):
    token = request.args.get('token')

    if token is None:
        raise Error("token require")

    try:
        attendee = Attendee.objects(token=token).get()
    except DoesNotExist:
        raise Error("invalid token")

    return attendee


@app.errorhandler(Error)
def handle_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/status')
def status():
    return get_attendee(request).to_json()


@app.route('/use/<scenario_id>')
def use(scenario_id):
    attendee = get_attendee(request)

    try:
        scenario = attendee.scenario[scenario_id]
    except KeyError:
        raise Error("invalid scenario_id")

    if scenario.used is not None:
        raise Error("has been used")

    scenario.used = time.time()
    attendee.save()

    return attendee.to_json()
