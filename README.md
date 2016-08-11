# CCIP-Server

A Community Checkin with Interactivity Project Server

## Pre-Requirement

* Ubuntu Server 14.04 LTS and above
* Python 3.4
* `pip install Flask mongoengine flask-mongoengine flask-cors`
* nginx
* uwsgi
* MongoDB

## Run

* `export FLASK_DEBUG=1` (optional)
* `export FLASK_APP=ccip.py`
* `flask run`
