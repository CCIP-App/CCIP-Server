import time
from error import Error
from flask import Flask, request, jsonify
from mongoengine.queryset import DoesNotExist
from models import db, Attendee

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)


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
