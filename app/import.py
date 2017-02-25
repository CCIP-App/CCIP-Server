import csv
import json

from flask import Flask
from models import db, Attendee, Scenario
from datetime import datetime

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)


def str2timestamp(str):
    return datetime.strptime(str, "%Y/%m/%d %H:%M %z").timestamp()


def bind_scenario(row, attendee, scenarios):
    for scenario_id, scenario in scenarios.items():
        sce = Scenario()
        sce.order = scenario['order']
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


def list_import(attendee_list, scenarios):
    for row in attendee_list:
        attendee = Attendee()
        attendee.token = row['token']
        if row['id'] == '':
            attendee.user_id = row['name']
        else:
            attendee.user_id = row['id']

        bind_scenario(row, attendee, scenarios)


def staff_import(attendee_list, scenarios):
    for row in attendee_list:
        attendee = Attendee()
        attendee.token = row['username']
        attendee.user_id = row['display_name']
        teams = row['groups'].split(',')

        try:
            teams.remove('工作人員')
            teams.remove('組長')
            teams.remove('股長')
        except ValueError:
            pass

        attendee.attr['teams'] = teams
        attendee.attr['title'] = row['title']

        bind_scenario(row, attendee, scenarios)


def from_csv(csv_file, scenarios, staff=False):
    list_import(csv.DictReader(csv_file), scenarios) if not staff else staff_import(csv.DictReader(csv_file), scenarios)


if __name__ == '__main__':
    import sys
    filename = sys.argv[1]
    scenario_filename = sys.argv[2]

    try:
        staff = bool(sys.argv[3])
    except IndexError:
        staff = False

    with open(filename, 'r') as csv_file, open(scenario_filename, 'r') as scenario_file:
        scenarios = json.load(scenario_file)
        from_csv(csv_file, scenarios, staff)
