import time
import json

from datetime import datetime
from error import Error
from flask import Flask, Response, request, jsonify
from mongoengine.queryset import DoesNotExist
from functools import wraps
from hashlib import sha1
from models import db, Attendee, Announcement, PuzzleStatus, PuzzleBucket
from mongoengine.queryset.visitor import Q
from random import randint

import config

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)

scenarios_def = {}
for type, filename in config.SCENARIO_DEFS.items():
    with open(filename) as json_file:
        scenarios_def[type] = json.load(json_file)


try:
    with open('puzzle-config.json', 'r') as puzzle_config_json:
        puzzle_config = json.load(puzzle_config_json)
except:
    puzzle_config = None
    app.logger.info('puzzle-config.json not found, not enable puzzle')

try:
    with open('delivery-permission.json', 'r') as delivery_permission_json:
        delivery_permission = json.load(delivery_permission_json)
except:
    delivery_permission = None
    app.logger.info('delivery-permission.json not found, can not deliver puzzle')

if puzzle_config is not None:
    puzzle_status_init = True if (PuzzleStatus.objects.count() == 0) else False

    base = 0
    for k, v in puzzle_config.items():
        base += v

    puzzle_rate = {}
    for k, v in puzzle_config.items():
        puzzle_rate[k] = v / base

        if puzzle_status_init:
            PuzzleStatus(puzzle=k).save()

    if puzzle_status_init:
        PuzzleStatus(puzzle='total').save()


def deliver_puzzle(attendee, deliverer=None):
    public_token = sha1(attendee.token.encode('utf-8')).hexdigest()

    try:
        puzzle_bucket = PuzzleBucket.objects(public_token=public_token).get()
    except DoesNotExist:
        puzzle_bucket = PuzzleBucket(attendee=attendee, public_token=public_token)

    if deliverer is not None:
        if deliverer in puzzle_bucket.deliverer:
            raise Error('Already take from this deliverer')
        else:
            puzzle_bucket.deliverer.append(deliverer)

    total = PuzzleStatus.objects(puzzle='total').get().quantity

    for i in range(len(puzzle_config)):
        puzzle = list(puzzle_config.keys())[randint(0, len(puzzle_config) - 1)]
        if i == len(puzzle_config) - 1 or total == 0 or PuzzleStatus.objects(puzzle=puzzle).get().quantity / total < puzzle_rate[puzzle]:
            puzzle_bucket.puzzle.append(puzzle)
            PuzzleStatus.objects(puzzle='total').update_one(inc__quantity=1)
            PuzzleStatus.objects(puzzle=puzzle).update_one(inc__quantity=1)
            break

    puzzle_bucket.save()


def returns_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        r = f(*args, **kwargs)
        return Response(r, content_type='application/json; charset=utf-8')
    return decorated_function


def get_puzzle_bucket(request):
    token = request.args.get('token')

    if token is None:
        raise Error("token required")

    try:
        puzzle_bucket = PuzzleBucket.objects(public_token=token).get()
    except DoesNotExist:
        raise Error("invalid token")

    return puzzle_bucket


def get_attendee(request):
    token = request.args.get('token')

    if token is None:
        raise Error("token required")

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


@app.route('/landing')
def landing():
    attendee = get_attendee(request)

    return jsonify({"nickname": attendee.user_id})


@app.route('/status')
@returns_json
def status():
    attendee = get_attendee(request)

    if not request.args.get('StaffQuery') and not attendee.first_use:
        attendee.first_use = time.time()
        attendee.save()

    return attendee.to_json()


@app.route('/use/<scenario_id>')
@returns_json
def use(scenario_id):
    attendee = get_attendee(request)

    try:
        scenario = attendee.scenario[scenario_id]
    except KeyError:
        raise Error("invalid scenario_id")

    if scenario.available_time <= time.time() and scenario.expire_time > time.time():
        if scenario.used is not None:
            raise Error("has been used")

        if scenario.disabled is not None:
            raise Error("disabled scenario")

        if scenarios_def[attendee.type].get(scenario_id).get('related_scenario'):
            for rsce in scenarios_def[attendee.type].get(scenario_id).get('related_scenario'):
                if rsce['unlock']:
                    attendee.scenario[rsce['id']].disabled = None

                if request.args.get('StaffQuery') and rsce.get('staff_query_used'):
                    attendee.scenario[rsce['id']].used = time.time()

                if rsce.get('disable_time') and time.time() > datetime.strptime(rsce['disable_time'], "%Y/%m/%d %H:%M %z").timestamp():
                    attendee.scenario[rsce['id']].disabled = rsce['disable_message']
                elif request.args.get('StaffQuery') and rsce.get('staff_query_disable_message'):
                    attendee.scenario[rsce['id']].disabled = rsce['staff_query_disable_message']

        if scenarios_def[attendee.type].get(scenario_id).get('deliver_puzzle') and puzzle_config is not None:
            for i in range(scenarios_def[attendee.type].get(scenario_id).get('deliver_puzzle')):
                deliver_puzzle(attendee)

        scenario.used = time.time()
        attendee.save()

        return get_attendee(request).to_json()
    else:
        raise Error("link expired/not available now")


@app.route('/event/puzzle')
def get_puzzle():
    puzzle_bucket = get_puzzle_bucket(request)

    return jsonify({
        "user_id": puzzle_bucket.attendee.user_id,
        "puzzle": puzzle_bucket.puzzle,
        "valid": puzzle_bucket.valid
    })


@app.route('/event/puzzle/revoke')
def revoke_puzzle():
    attendee = get_attendee(request)

    public_token = sha1(attendee.token.encode('utf-8')).hexdigest()

    try:
        puzzle_bucket = PuzzleBucket.objects(public_token=public_token).get()
    except DoesNotExist:
        raise Error("invalid token")

    puzzle_bucket.valid = False

    puzzle_bucket.save()

    return jsonify({'status': 'OK'})


@app.route('/event/puzzle/deliverer')
def get_deliverer():
    token = request.args.get('token')

    if token is None:
        raise Error("token required")

    if token in delivery_permission.keys():
        return jsonify({'display_name': delivery_permission[token]})
    else:
        raise Error("invalid token")


@app.route('/event/puzzle/deliver', methods=['POST'])
def do_deliver_puzzle():
    token = request.args.get('token')
    receiver = request.form.get('receiver')

    if token is None or receiver is None:
        raise Error("token and receiver required")

    try:
        attendee = Attendee.objects(token=receiver).get()
    except DoesNotExist:
        raise Error("invalid receiver token")

    if token in delivery_permission.keys():
        deliver_puzzle(attendee, token)
        app.logger.info(delivery_permission[token] + ' ' + token + ' deliver puzzle to ' + attendee.token)
        return jsonify({'status': 'OK'})
    else:
        raise Error("invalid token")


@app.route('/event/puzzle/dashboard')
@returns_json
def get_puzzle_dashboard():
    puzzle_status = PuzzleStatus.objects()

    return puzzle_status.to_json()


@app.route('/announcement', methods=['GET', 'POST'])
def announcement():
    if request.method == 'GET':
        return jsonify(Announcement.objects().order_by('-_id'))
    if request.method == 'POST':
        announcement = Announcement()
        announcement.datetime = time.time()
        announcement.msg_zh = request.form.get('msg_zh')
        announcement.msg_en = request.form.get('msg_en')
        announcement.uri = request.form.get('uri')
        announcement.save()

        return jsonify({'status': 'OK'})


@app.route('/dashboard')
def dashboard():
    res = {}
    res['total'] = Attendee.objects().count()
    res['day1checkin_used'] = Attendee.objects(scenario__day1checkin__used__ne=None).count()
    res['kit_used'] = Attendee.objects(scenario__kit__used__ne=None).count()
    res['day1lunch'] = {
        'total': Attendee.objects(Q(scenario__day1lunch__disabled=None) | Q(scenario__day1lunch__disabled="Please use your badge")).count(),
        'meat': Attendee.objects(Q(scenario__day1lunch__attr__diet="meat") & (Q(scenario__day1lunch__disabled="Please use your badge") | Q(scenario__day1lunch__disabled=None))).count(),
        'vegetarian': Attendee.objects(Q(scenario__day1lunch__attr__diet="vegetarian") & (Q(scenario__day1lunch__disabled="Please use your badge") | Q(scenario__day1lunch__disabled=None))).count(),
        'meat_used': Attendee.objects(scenario__day1lunch__attr__diet="meat", scenario__day1lunch__used__ne=None).count(),
        'vegetarian_used': Attendee.objects(scenario__day1lunch__attr__diet="vegetarian", scenario__day1lunch__used__ne=None).count(),
    }
    res['day2checkin_used'] = Attendee.objects(scenario__day2checkin__used__ne=None).count()
    res['day2lunch'] = {
        'total': Attendee.objects(Q(scenario__day2lunch__disabled=None) | Q(scenario__day2lunch__disabled="Please use your badge")).count(),
        'meat': Attendee.objects(Q(scenario__day2lunch__attr__diet="meat") & (Q(scenario__day2lunch__disabled="Please use your badge") | Q(scenario__day2lunch__disabled=None))).count(),
        'vegetarian': Attendee.objects(Q(scenario__day2lunch__attr__diet="vegetarian") & (Q(scenario__day2lunch__disabled="Please use your badge") | Q(scenario__day2lunch__disabled=None))).count(),
        'meat_used': Attendee.objects(scenario__day2lunch__attr__diet="meat", scenario__day2lunch__used__ne=None).count(),
        'vegetarian_used': Attendee.objects(scenario__day2lunch__attr__diet="vegetarian", scenario__day2lunch__used__ne=None).count(),
    }
    res['vipkit'] = {
        'total': Attendee.objects(scenario__vipkit__disabled=None).count(),
        'used': Attendee.objects(scenario__vipkit__used__ne=None).count()
    }
    res['logged'] = Attendee.objects().count() - Attendee.objects(first_use=None).count()

    return jsonify(res)


@app.route('/scenarios')
def scenarios():
    try:
        return jsonify(list(scenarios_def[request.args.get('type')].keys()))
    except:
        raise Error("type required")
