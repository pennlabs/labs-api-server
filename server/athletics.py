from flask import jsonify
from base import *
from server import app
from pennathletics import athletes
from flask import request
from pennathletics import sportsdata
from pennathletics import scraper

@app.route('/athletics')
def get_sports():
    return jsonify({"sports": sportsdata.SPORTS.keys()}) 

@app.route('/athletics/<sport_id>')
def list_years(sport_id):
    return jsonify({"years": scraper.get_years(sport_id)}) 

@app.route('/athletics/<sport_id>/<year>')
def search_players(sport_id, year):
    params = request.args;
    new_dict = dict((k,v) for k,v in params.items())
    if 'no' in new_dict:
        new_dict['no'] = int(new_dict['no'])
    if 'weight' in params:
        new_dict['weight'] = int(new_dict['weight'])
    list_players = athletes.get_player(sport_id, year, **new_dict)
    list_to_return = [athlete.__dict__ for athlete in list_players]
    return jsonify({"athletes": list_to_return})

@app.route('/athletics/<sport_id>/<year>/roster')
def return_roster(sport_id, year):
    roster = athletes.get_roster(sport_id, year)
    roster_json = [athlete.__dict__ for athlete in roster]
    return jsonify({"athletes": roster_json})

@app.route('/athletics/<sport_id>/<year>/schedule')
def return_schedule(sport_id, year):
    return jsonify({"schedule": scraper.get_schedule(sport_id, year)})
