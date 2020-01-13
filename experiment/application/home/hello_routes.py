from .forms import MainMenuForm
from flask import Blueprint, render_template, flash, redirect, request, session, url_for, make_response, current_app, g
from datetime import datetime
import numpy as np
import os
import pymongo
import pickle
from wtforms import RadioField, BooleanField, SubmitField, StringField, SelectField, Form
from application.db import get_db
from application import mongo

#name of Blueprint obj = "hello_bp"
hello_bp = Blueprint('hello_bp', __name__,
                     template_folder='templates', static_folder='static')

select_dict = {}

#access the mongodb via app.mongo
@hello_bp.route('/',methods=['GET','POST'])
def landing():
    #render templates /home/landingPage.html; as explained at the bottom: https://flask.palletsprojects.com/en/1.0.x/blueprints/
    def get_db_connection():
        con = getattr(g, 'mongo', None)
        if con is None:
            g.con = con = connection_pool.get_connection()
        return con
    
    #db = get_db()
    form = MainMenuForm(csrf_enabled=False)
    assert form is not None, "MainMenuForm object is none"
    assert form.team1_selection is not None, "form object doesn't contain team1_selection attribute"
    assert type(form.team1_selection) is SelectField, "team1 selection is not a field object"
    #in order for current_app to be available, a request must have been issued... app_context must be instantiated... should test whether it's available somewhere in code... KIM ea request gets its own application context. The app_context can stand on its own w/o the request context
    teamlist = sorted(list(mongo.db['teststats'].distinct('teamname')))
    #convert list to a list of tuples... THIS NEEDS TO BE TESTED AGAIN
    team_tups = [(i,val) for i, val in enumerate(teamlist,1)]
    form.team1_selection.choices = team_tups
    form.team2_selection.choices = team_tups
    if form.validate_on_submit():
    #need to store user selection
        opponent1 = dict(team_tups).get(form.team1_selection.data)
        opponent2 = dict(team_tups).get(form.team2_selection.data)
        #render results output and pass the selection values
        teams = [opponent1, opponent2]
        print("from landing route, teams are of type {}: {}".format(type(teams),teams))
        #return(redirect(url_for('hello_bp.rawStats', teams = teams)))
        return redirect(url_for('hello_bp.rawStats', opponent1 = opponent1, opponent2 = opponent2))
    return(render_template('/home/landingPage.html', form = form))
    

@hello_bp.route('/stats/<opponent1>/<opponent2>',methods=['GET','POST'])
def rawStats(opponent1,opponent2):
    #although we pass opponents explicitly here, could probably query the request object to this route
    #next challenge is to post a link on this page that renders the stat rankings pages for ea team... that may actually be a different view
    return render_template('/home/selection.html',opponent_html1 = opponent1, opponent_html2 = opponent2)

@hello_bp.route('/statsSelected', methods = ['GET','POST'])
def statsLink():
    #this page is currently served up via a hyperlink in the html template
    #place the stats from the query results here
    with open('/home/merde/Documents/ncaaf/flask_app/experiment/application/home/objects/clemsonList.pickle', 'rb') as filename:
        clemson = pickle.load(filename)
        
    with open('/home/merde/Documents/ncaaf/flask_app/experiment/application/home/objects/floridaList.pickle', 'rb') as filename:
        florida = pickle.load(filename)
    #return(render_template('/home/statsPage.html'))
    return render_template('/home/oneTable.html',florida = florida, clemson = clemson, zippedlist = zip(florida, clemson)) 
    
@hello_bp.route('/selectedTeamStats/<opponent1>/<opponent2>', methods = ['GET','POST'])
def teamsSelected(opponent1, opponent2):    
    def extractToCSV(opponent1, opponent2):
        ''' 1. query the database and extract team stats  a/o latest date
    2. separate each team into its own container
    3. sort the container so that team list matches same order
    4. measure the longest dict in ea container
    5. write each list of dicts to csv in format encoded'''
        pipeline = [{"$match":{'teamname':{"$in":[opponent1, opponent2]}}}, 
        {"$project": {"teamname": 1, "stats_list": { "$filter":{"input":'$stats_list', 
            "cond":{"$eq":["$$this.games_through",datetime.strptime("2019-10-19","%Y-%m-%d")]}}}}}]
        test = mongo.db['teststats'].aggregate(pipeline)
        lista_test = list(test)
    
    #names may cross at some point, so redefining here for labels later on
        new_team1=lista_test[0]['teamname']
        new_team2=lista_test[1]['teamname']
    
        team1_li = lista_test[0]['stats_list']
        team2_li = lista_test[1]['stats_list'] # will return a dict element
    
    #select the team w/the shortest list to compose the sorted_list; if not, may generate key value errors later... forsort is set to the df w/the fewest records
        forsort = (team1_li,team2_li)[np.argmin((len(team1_li),len(team2_li)))]
    #extract the stat headers of the shortest df
        sorted_list = sorted([i['statlabel'] for i in forsort])
    #iterate two objects: 1) stats headers 2) stats dict for the team
        tm1_sorted = [stat for i in sorted_list for stat in team1_li if stat['statlabel'] ==i]
    #iterate two objects: 1) stats headers 2) stats dict for the team
        tm2_sorted = [stat for i in sorted_list for stat in team2_li if stat['statlabel'] ==i]
        return((new_team1, new_team2, tm1_sorted,tm2_sorted))
    teamName1, teamName2, team1, team2 = extractToCSV(opponent1, opponent2)
    return render_template('/home/twoTable.html', containedList = [team1, team2], teamNameList = [teamName1, teamName2]) 
