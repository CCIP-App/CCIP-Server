import time
import json

from datetime import datetime
from error import Error
from flask import Flask, Response, request, jsonify
from mongoengine.queryset import DoesNotExist
from functools import wraps
from models import db, Attendee, Announcement, PuzzleStatus, PuzzleBucket
from random import randint

import config

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)

scenarios_def = {}
for role, filename in config.SCENARIO_DEFS.items():
    with open(filename) as json_file:
        scenarios_def[role] = json.load(json_file)


try:
    with open('puzzle-config.json', 'r') as puzzle_config_json:
        puzzle_config = json.load(puzzle_config_json)
except IOError:
    puzzle_config = None
    app.logger.info('puzzle-config.json not found, not enable puzzle')

try:
    with open('delivery-permission.json', 'r') as delivery_permission_json:
        delivery_permission = json.load(delivery_permission_json)
except IOError:
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
    try:
        puzzle_bucket = PuzzleBucket.objects(public_token=attendee.public_token).get()
    except DoesNotExist:
        puzzle_bucket = PuzzleBucket.init(attendee)

    if deliverer is not None:
        if deliverer in list(map(lambda d: d['deliverer'], puzzle_bucket.deliverer)):
            raise Error('Already take from this deliverer')
        else:
            puzzle_bucket.deliverer.append({
                "deliverer": deliverer,
                "timestamp": time.time()
            })

    total = PuzzleStatus.objects(puzzle='total').get().quantity

    for i in range(len(puzzle_config)):
        puzzle = list(puzzle_config.keys())[randint(0, len(puzzle_config) - 1)]
        if i == len(puzzle_config) - 1 or total == 0 or PuzzleStatus.objects(puzzle=puzzle).get().currency / total < puzzle_rate[puzzle]:
            puzzle_bucket.puzzle.append(puzzle)
            PuzzleStatus.objects(puzzle='total').update_one(inc__quantity=1, inc__currency=1)
            PuzzleStatus.objects(puzzle=puzzle).update_one(inc__quantity=1, inc__currency=1)
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
        raise Error("Invalid token, please try again after checkin.")

    return puzzle_bucket


def get_puzzle_bucket_by_attendee(attendee):
    try:
        puzzle_bucket = PuzzleBucket.objects(public_token=attendee.public_token).get()
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

        PuzzleBucket.init(attendee)

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

        if scenarios_def[attendee.role].get(scenario_id).get('related_scenario'):
            for rsce in scenarios_def[attendee.role].get(scenario_id).get('related_scenario'):
                if rsce['unlock']:
                    attendee.scenario[rsce['id']].disabled = None

                if request.args.get('StaffQuery') and rsce.get('staff_query_used') and attendee.scenario[rsce['id']].used is None:
                    attendee.scenario[rsce['id']].used = time.time()

                if rsce.get('disable_time') and time.time() > datetime.strptime(rsce['disable_time'], "%Y/%m/%d %H:%M %z").timestamp():
                    attendee.scenario[rsce['id']].disabled = rsce['disable_message']
                elif request.args.get('StaffQuery') and rsce.get('staff_query_disable_message'):
                    attendee.scenario[rsce['id']].disabled = rsce['staff_query_disable_message']

        if scenarios_def[attendee.role].get(scenario_id).get('deliver_puzzle') and puzzle_config is not None:
            for i in range(scenarios_def[attendee.role].get(scenario_id).get('deliver_puzzle')):
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
        "puzzles": puzzle_bucket.puzzle,
        "deliverers": puzzle_bucket.deliverer,
        "valid": puzzle_bucket.valid,
        "coupon": puzzle_bucket.coupon
    })


@app.route('/event/puzzle/revoke')
def revoke_puzzle():
    attendee = get_attendee(request)

    puzzle_bucket = get_puzzle_bucket_by_attendee(attendee)

    PuzzleStatus.objects(puzzle='total').update_one(dec__currency=len(puzzle_bucket.puzzle))
    for puzzle in puzzle_bucket.puzzle:
        PuzzleStatus.objects(puzzle=puzzle).update_one(dec__currency=1)

    puzzle_bucket.valid = time.time()
    puzzle_bucket.coupon = 0

    puzzle_bucket.save()

    return jsonify({'status': 'OK'})


@app.route('/event/puzzle/coupon')
def use_coupon():
    attendee = get_attendee(request)

    puzzle_bucket = get_puzzle_bucket_by_attendee(attendee)

    puzzle_bucket.coupon = time.time()
    puzzle_bucket.save()

    return jsonify({'status': 'OK'})


@app.route('/event/puzzle/deliverer')
def get_deliverer():
    token = request.args.get('token')

    if token is None:
        raise Error("token required")

    if token in delivery_permission.keys():
        return jsonify({'slug': delivery_permission[token]})
    else:
        raise Error("invalid deliverer token")


@app.route('/event/puzzle/deliverers')
def get_deliverers():
    return jsonify(list(delivery_permission.values()))


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
        deliver_puzzle(attendee, delivery_permission[token])
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
        token = request.args.get('token')
        role = config.ANNOUNCEMENT_DEFAULT_ROLE

        if token is not None:
            try:
                attendee = Attendee.objects(token=token).get()
                role = attendee.role
            except DoesNotExist:
                raise Error("invalid token")

        return jsonify(Announcement.objects(role=role).order_by('-_id'))

    if request.method == 'POST':
        announcement = Announcement()
        announcement.datetime = time.time()
        announcement.msg_zh = request.form.get('msg_zh')
        announcement.msg_en = request.form.get('msg_en')
        announcement.uri = request.form.get('uri')
        announcement.role = request.form.getlist('role[]')
        announcement.save()

        return jsonify({'status': 'OK'})


def role_stats(role):
    res = {
        'role': role,
        'total': Attendee.objects(role=role).count(),
        'logged': Attendee.objects(role=role, first_use__ne=None).count(),
        'scenarios': []
    }

    for scenario in scenarios_def[role]:
        query_enabled_args = {
            'role': role,
            'scenario__{}__disabled'.format(scenario): None
        }

        query_used_args = {
            'role': role,
            'scenario__{}__used__ne'.format(scenario): None
        }

        res['scenarios'].append({
            'scenario': scenario,
            'enabled': Attendee.objects(**query_enabled_args).count(),
            'used': Attendee.objects(**query_used_args).count()
        })

    return res


@app.route('/dashboard')
def dashboard():
    return jsonify(list(map(role_stats, scenarios_def.keys())))


@app.route('/dashboard/<role>')
def dashboard_role(role):

    if role not in scenarios_def:
        raise Error('role required')

    scenarios = scenarios_def[role]

    req_fields = ['event_id', 'user_id', 'attr'] + \
        list(map(lambda str: 'scenario__' + str + '__used', scenarios)) + \
        list(map(lambda str: 'scenario__' + str + '__attr', scenarios)) \

    return jsonify(Attendee.objects(role=role).only(*req_fields))


@app.route('/roles')
def roles():
    return jsonify(list(scenarios_def.keys()))


@app.route('/scenarios')
def scenarios():
    try:
        return jsonify(list(scenarios_def[request.args.get('role')].keys()))
    except KeyError:
        raise Error("role required")
