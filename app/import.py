import csv
import json
import os

from flask import Flask
from models import db, Attendee, Scenario
from datetime import datetime

import config

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)

scenarios_def = {}
for role, filename in config.SCENARIO_DEFS.items():
    with open(filename) as json_file:
        scenarios_def[role] = json.load(json_file)


def str2timestamp(str):
    return datetime.strptime(str, "%Y/%m/%d %H:%M %z").timestamp()


def bind_scenario(row, attendee, scenarios):
    for scenario_id, scenario in scenarios.items():
        sce = Scenario()

        if scenario.get('show_rule'):
            if row[scenario.get('show_rule')['row_name']] != scenario.get('show_rule')['value_match']:
                continue

        sce.order = scenario['order']
        sce.display_text = scenario['display_text']
        sce.available_time = str2timestamp(scenario['available_time'])
        sce.expire_time = str2timestamp(scenario['expire_time'])
        sce.countdown = scenario['countdown']

        if scenario.get('lock_message'):
            sce.disabled = scenario.get('lock_message')

        if scenario.get('attr'):
            for attr in scenario.get('attr'):
                if not attr.get('value'):
                    sce.attr[attr['attr_name']] = row[attr['row_name']]

                else:
                    sce.attr[attr['attr_name']] = attr.get('value')[row[attr['row_name']]]

        if scenario.get('not_lock_rule'):
            if row[scenario.get('not_lock_rule')['row_name']] == scenario.get('not_lock_rule')['value_match']:
                sce.disabled = None
            else:
                sce.disabled = scenario.get('not_lock_rule')['not_match_disable_message']

        attendee.scenario[scenario_id] = sce

    attendee.save()


def list_import(attendee_list, role):
    for row in attendee_list:
        attendee = Attendee()
        attendee.event_id = os.environ['EVENT_ID']
        attendee.token = row['token']

        try:
            attendee.attr['title'] = row['title']
        except KeyError:
            pass
        attendee.user_id = row['display_name']

        attendee.role = role

        bind_scenario(row, attendee, scenarios_def[role])


if __name__ == '__main__':
    import sys

    try:
        os.environ['EVENT_ID']
    except KeyError:
        print("export EVENT_ID in env")
        exit(1)

    filename = sys.argv[1]
    role = sys.argv[2]

    with open(filename, 'r') as csv_file:
        list_import(csv.DictReader(csv_file), role)
