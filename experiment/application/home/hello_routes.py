from .forms import MainMenuForm
from flask import Blueprint, render_template, flash, redirect, request, session, url_for, make_response, current_app, g
from datetime import datetime
import numpy as np
import os
import pymongo
import plotly.express as px
import pickle
import pandas as pd
from wtforms import RadioField, BooleanField, SubmitField, StringField, SelectField, Form
from application.db import get_db
from application import mongo

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
        ''' 1. query the database and extract team stats a/o latest date
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
        #function extractToCSV terminated w/above line
        
    teamName1, teamName2, ncaa_rank_coll_team1, ncaa_rank_coll_team2 = extractToCSV(opponent1, opponent2)
    
    #session level variable
    ncaa_rank_coll_team_list.append(ncaa_rank_coll_team1)
    ncaa_rank_coll_team_list.append(ncaa_rank_coll_team2)
    #teamName1 and teamName2 above are the data tables
    return render_template('/home/twoTable.html', containedList = [team1, team2], teamNameList = [teamName1, teamName2]) 

@hello_bp.route('/mirrorChart/<opponent1>/<opponent2>', methods = ['GET','POST'])
def renderMirror(opponent1, opponent2):
    #each element of the stats_list (44 elements for each list) is a dictionary of compartmentalized stats of a particular category and aren't normalized to readily convert to df, so must loop through ea element within the list (separate dictionaries) and cherry pick the attribute of the category I care about
    def extract(dic):
        return [k for g,k in dic.items() if g in ['statlabel','Rank']]
    
    team1 = [extract(k) for k in lista_test[0]['stats_list']]
    team2 = [extract(k) for k in lista_test[1]['stats_list']]
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
    
    data = [
    go.Bar(x=test['rank1'], y=test.index, name=lista_test[0]['teamname']+ ' Ranks',  
            orientation = "h", text = test['rank1'], textposition = 'outside'
           ),
    go.Bar(x=test['rank2'], y=test.index, name=lista_test[1]['teamname']+' Ranks', 
           orientation = "h", text = abs(test['rank2']), textposition = 'outside'
          )]
layout = go.Layout(
    barmode='overlay', height = 900, title = go.layout.Title(text="Side-by-side rankings")
)

fig = go.Figure(dict(data = data, layout = layout))

fig.update_layout(
    xaxis = dict(
        tickmode = 'array',
        tickvals = [-100,-75,-50,-25,0, 25, 50, 75, 100],
        ticktext = ['100', '75','50','25','0','25', '50', '75', '100']
    )
)


    return()
