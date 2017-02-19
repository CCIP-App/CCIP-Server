import csv
import json

from flask import Flask
from models import db, Attendee, Scenario
from datetime import datetime

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)


def str2timestamp(str):
    return datetime.strptime(str, "%Y/%m/%d %H:%M").timestamp()


def list_import(attendee_list):
    for row in attendee_list:
        attendee = Attendee()
        attendee.token = row['token']
        if row['id'] == '':
            attendee.user_id = row['name']
        else:
            attendee.user_id = row['id']

        with open('scenario.json') as json_file:
            scenarios = json.load(json_file)

        for i, scenario_id in enumerate(scenarios.keys()):
            scenario = scenarios[scenario_id]

            sce = Scenario()
            sce.order = i
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


def staff_import(attendee_list):
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

        sce1 = Scenario()
        sce1.order = 1
        sce1.available_time = str2timestamp("2016/08/20 8:30")
        sce1.expire_time = str2timestamp("2016/08/20 15:00")
        sce1.countdown = 0
        attendee.scenario['day1checkin'] = sce1

        sce2 = Scenario()
        sce2.order = 2
        sce2.available_time = str2timestamp("2016/08/20 8:30")
        sce2.expire_time = str2timestamp("2016/08/20 15:00")
        sce2.disabled = "Haven't Check-in"
        sce2.countdown = 60
        sce2.attr['shirt_size'] = row['shirt_size']
        attendee.scenario['kit'] = sce2

        sce3 = Scenario()
        sce3.order = 3
        sce3.available_time = str2timestamp("2016/08/20 11:30")
        sce3.expire_time = str2timestamp("2016/08/20 14:00")
        sce3.disabled = "Haven't Check-in"
        sce3.countdown = 60
        if row['diet'] == '葷':
            sce3.attr = {"diet": "meat"}
        else:
            sce3.attr = {"diet": "vegetarian"}
        attendee.scenario['day1lunch'] = sce3

        sce4 = Scenario()
        sce4.order = 4
        sce4.available_time = str2timestamp("2016/08/21 8:30")
        sce4.expire_time = str2timestamp("2016/08/21 15:00")
        sce4.countdown = 0
        attendee.scenario['day2checkin'] = sce4

        sce5 = Scenario()
        sce5.order = 5
        sce5.available_time = str2timestamp("2016/08/21 11:30")
        sce5.expire_time = str2timestamp("2016/08/21 14:00")
        sce5.disabled = "Haven't Check-in"
        sce5.countdown = 60
        if row['diet'] == '葷':
            sce5.attr = {"diet": "meat"}
        else:
            sce5.attr = {"diet": "vegetarian"}
        attendee.scenario['day2lunch'] = sce5

        sce6 = Scenario()
        sce6.order = 6
        sce6.available_time = str2timestamp("2016/08/20 8:30")
        sce6.expire_time = str2timestamp("2016/08/21 15:00")
        sce6.disabled = "For Supporters Only"
        sce6.countdown = 60
        attendee.scenario['vipkit'] = sce6

        attendee.save()


def from_csv(csv_file, staff=False): list_import(csv.DictReader(csv_file)) if not staff else staff_import(csv.DictReader(csv_file))

if __name__ == '__main__':
    import sys
    filename = sys.argv[1]

    try:
        staff = bool(sys.argv[2])
    except IndexError:
        staff = False

    with open(filename, 'r') as csv_file:
        from_csv(csv_file, staff)
