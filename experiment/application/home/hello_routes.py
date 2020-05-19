from .forms import MainMenuForm
from flask import Blueprint, render_template, flash, redirect, request, session, url_for, make_response, current_app, g
from datetime import datetime
import numpy as np
import os
import pymongo
import plotly.express as px
import plotly.graph_objects as go
import pickle
import plotly
import pandas as pd
from wtforms import RadioField, BooleanField, SubmitField, StringField, SelectField, Form
from application.db import get_db
#mongo is instantiated as a global variable in the application/__init__.py... it's possible that bc the blueprint is registered within the app_context, that this module has access to mongo
from application import mongo
import json

#name of Blueprint obj = "hello_bp"
hello_bp = Blueprint('hello_bp', __name__,
                     template_folder='templates', static_folder='static')

select_dict = {}
ncaa_rank_coll_team_list = []

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
    #this page is currently served up via a hyperlink in the selection.html template
    #place the stats from the query results here
    with open('/home/merde/Documents/ncaaf/flask_app/experiment/application/home/objects/clemsonList.pickle', 'rb') as filename:
        clemson = pickle.load(filename)
        
    with open('/home/merde/Documents/ncaaf/flask_app/experiment/application/home/objects/floridaList.pickle', 'rb') as filename:
        florida = pickle.load(filename)
    #return(render_template('/home/statsPage.html'))
    return render_template('/home/oneTable.html',florida = florida, clemson = clemson, zippedlist = zip(florida, clemson)) 
    
@hello_bp.route('/selectedTeamStats/<opponent1>/<opponent2>', methods = ['GET','POST'])
def teamsSelected(opponent1, opponent2):    
    #this page is currently served up via a hyperlink in the selection.html template
    def extractToCSV(opponent1, opponent2):
        ''' 1. query the database and extract team stats  a/o latest date
    2. separate each team into its own container
    3. sort the container so that team list matches same order
    4. measure the longest dict in ea container
    5. write each list of dicts to csv in format encoded'''
        pipeline = [{"$match":{'teamname':{"$in":[opponent1, opponent2]}}}, 
        {"$project": {"teamname": 1, "stats_list": { "$filter":{"input":'$stats_list', 
            "cond":{"$eq":["$$this.games_through",datetime.strptime("2019-11-30","%Y-%m-%d")]}}}}}]
        test = mongo.db['teststats'].aggregate(pipeline)
        lista_test = list(test)
    
    #names may cross at some point, so redefining here for labels later on
        new_team1=lista_test[0]['teamname']
        new_team2=lista_test[1]['teamname']
    
        team1_li = lista_test[0]['stats_list']
        team2_li = lista_test[1]['stats_list'] # will return a dict element
        teamDataDict = {new_team1:team1_li,new_team2:team2_li}

#select the team w/the shortest list to compose the sorted_list; if not, may generate key value errors later... forsort is set to the df w/the fewest records... and so the order may be rearranged
        forsort = ((new_team1,team1_li),(new_team2,team2_li))[np.argmin((len(team1_li),len(team2_li)))]
        newFirstTeam = forsort[0]
        newSecondTeam = [i for i in teamDataDict.keys() if i != forsort[0]][0]
#extract the stat headers of the shortest df
#iterate two objects: 1) stats headers 2) stats dict for the team
        sorted_list = sorted([i['statlabel'] for i in forsort[1]])
    #iterate two objects: 1) stats headers 2) stats dict for the team
        tm1_sorted = [stat for i in sorted_list for stat in forsort[1] if stat['statlabel'] ==i]
#iterate two objects: 1) stats headers 2) stats dict for the team
        tm2_sorted = [stat for i in sorted_list for stat in     teamDataDict[newSecondTeam] if stat['statlabel'] ==i]
            
        return((forsort[0],newSecondTeam,tm1_sorted,tm2_sorted))
        #function extractToCSV terminated w/above line
        
    teamName1, teamName2, ncaa_rank_coll_team1, ncaa_rank_coll_team2 = extractToCSV(opponent1, opponent2)
    
    #session level variable: store the collection (unknown data format at this point) at a session-level dict
    ncaa_rank_coll_team_list.clear()
    ncaa_rank_coll_team_list.append(ncaa_rank_coll_team1)
    ncaa_rank_coll_team_list.append(ncaa_rank_coll_team2)
    #teamName1 and teamName2 above are the data tables
    return render_template('/home/twoTable.html', containedList = [ncaa_rank_coll_team1, ncaa_rank_coll_team2], teamNameList = [teamName1, teamName2]) 

@hello_bp.route('/mirrorChart/<opponent1>/<opponent2>', methods = ['GET','POST'])
def renderMirror(opponent1, opponent2):
    #each element of the stats_list (44 elements for each list) is a dictionary of compartmentalized stats of a particular category and aren't normalized to readily convert to df, so must loop through ea element within the list (separate dictionaries) and cherry pick the attribute of the category I care about
    def extract(dic):
        return [k for g,k in dic.items() if g in ['statlabel','Rank']]
    #ncaa_rank_coll_team_list is a session-level list
    team1 = [extract(k) for k in ncaa_rank_coll_team_list[0]]
    team2 = [extract(k) for k in ncaa_rank_coll_team_list[1]]
    df1 = pd.DataFrame(team1, columns = ['statlabel','rank1'])
    df2 = pd.DataFrame(team2, columns = ['statlabel','rank2'])
    
    #Concatenate the two separate team dataframes into one, and allow the rogue stat with a counterpart in each dataframe to dangle.
    #set the row indexes equal to the statlabel so I can concatenate properly
    df1.set_index('statlabel', inplace = True)
    df2.set_index('statlabel', inplace = True)
    
    test = pd.concat([df1,df2], axis = 1)
    test['diff'] = abs(test['rank2'] - test['rank1'])
    test['rank2'] = test['rank2'] * -1

    #add a categorical variable for the size of the discrepancy between rankings; 
    #this variable will be used later to highlight bars on the barchart
    cut_bins=[0,60,100]
    cut_labels = ['normal','pronounced']
    test['rank_disp'] = pd.cut(test['diff'], bins=cut_bins,     labels=cut_labels)
    
    #the user defined "data" list and layout variable will be inserted as k,v in dict stored within figList
    data = [
    go.Bar(x=test['rank1'], y=test.index, name=opponent1+ ' Ranks',  
            orientation = "h", text = test['rank1'], textposition = 'outside'
           ),
    go.Bar(x=test['rank2'], y=test.index, name=opponent2+' Ranks', 
           orientation = "h", text = abs(test['rank2']), textposition = 'outside'
          )]
    layout = go.Layout(barmode='overlay', height = None, title = go.layout.Title(text="Side-by-side rankings"), margin=dict(l = 200),
    xaxis = dict(
        tickmode = 'array',
        tickvals = [-100,-75,-50,-25,0, 25, 50, 75, 100],
        ticktext = ['100', '75','50','25','0','25', '50', '75', '100']
    )
)

    #fig = go.Figure(dict(data = data, layout = layout))
    #original version above, json encoding input below
    #figList here follows the format from https://github.com/plotly/plotlyjs-flask-example/blob/master/app.py
    figList = [dict(data = data, layout = layout)]

    #cls argument is a custom JSONEncoder subclass
    #json dumps accepts as the obj argument a serializable python object; the native JSONEncoder class supports dict, list, tuple, etc ob... the subsequent script at the top of the html template does the work of go.Figure() - utilized in a standalone operation
    graphJSON = json.dumps(figList, cls = plotly.utils.PlotlyJSONEncoder)

    return(render_template('/home/mirrorPlot.html',plot = graphJSON))
