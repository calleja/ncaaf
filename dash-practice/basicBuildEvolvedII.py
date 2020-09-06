#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Dash server that utilizes a previously established Flask server from flask_server.py
This program was built on top of basicBuildDash.py
This program demonstrates how functions can be scoped at the highest level

7/7: Implement the mongo query/pipeline from the pymongoWork_nestedCollections... file. The query and result set is pulled up front. A chart with a defaulted set of action is rendered. Additionally, users can select a week of action from a drop down. Hopefully this can all be contained on the same dash page. 
Need to devise some kind of lookup table where week number corresponds with a date of play
'''
import dash
import dash_core_components as dcc
import dash_html_components as html
import pymongo
import numpy as np
import datetime
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output
#from application import mongo <- future iterations


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

def controller(server):
    dash_app = dash.Dash(__name__,
                         server=server,
                         routes_pathname_prefix='/',
                         external_stylesheets=['/static/css/styles.css']
                         )
    
    dash_app.layout = html.Div(children=[
    dcc.Location(id='url', refresh=False),
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

#candidate object though which to render new plots
    dcc.Graph(
        id='my-output')])
    
#Output is a dcc object
    @dash_app.callback(Output(component_id='my-output', component_property='figure'), [Input('url', 'href')])
    #no input here...
    def create_dashboard(href):
        #split the url to extract the team names
        try:
            lista = href.split("/")
            opp1,opp2 = list(filter(None, lista))[-2:]
            opponent1, opponent2, df_opponents = compileData(opp1, opp2)
        except (IndexError, AttributeError) as e:
            opponent1, opponent2, df_opponents = compileData('Rutgers','Florida')

        data = [go.Bar(x=df_opponents['rank1'], y=df_opponents.index, name=opponent1+ ' Ranks', orientation = "h", text = df_opponents['rank1'], textposition = 'outside'
           ), go.Bar(x=df_opponents['rank2'], y=df_opponents.index, name=opponent2+' Ranks', 
           orientation = "h", text = abs(df_opponents['rank2']), textposition = 'outside'
          )]
                     
        layout = go.Layout(barmode='overlay', height = None, title = go.layout.Title(text="Side-by-side rankings"), margin=dict(l = 200),
    xaxis = dict(
        tickmode = 'array',
        tickvals = [-100,-75,-50,-25,0, 25, 50, 75, 100],
        ticktext = ['100', '75','50','25','0','25', '50', '75', '100']
        )
        )
        fig = go.Figure(dict(data = data, layout = layout))
        return fig
    return dash_app.server

def connectDB():
    mongo = pymongo.MongoClient("mongodb://localhost:27017/stageprod_agg")
    print("connection established, proven via: {} ",format(mongo.server_info()))
    return(mongo)

def compileData(opponent1,opponent2):
    #has hard coded the two opponents
    def extract(dic):
        return [k for g,k in dic.items() if g in ['statlabel','Rank']]
    
    #teamName1, teamName2, ncaa_rank_coll_team1, ncaa_rank_coll_team2 = extractToCSV('Clemson','Florida')
    print('two team names provided to compileData(): {},{}'.format(opponent1,opponent2))
    teamName1, teamName2, ncaa_rank_coll_team1, ncaa_rank_coll_team2 = extractToCSV(opponent1,opponent2)
    #ncaa_rank_coll_team_list is a session-level list
    team1 = [extract(k) for k in ncaa_rank_coll_team1]
    team2 = [extract(k) for k in ncaa_rank_coll_team2]
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
    return((teamName1, teamName2, test))

#object declared outside of local function scope; however it worked in basicBuildDash
mongo = connectDB()

def extractToCSV(opponent1, opponent2):
    ''' 1. query the database and extract team stats  a/o latest date
    2. separate each team into its own container
    3. sort the container so that team list matches same order
    4. measure the longest dict in ea container
    5. write each list of dicts to csv in format encoded'''
    pipeline = [{"$match":{'teamname':{"$in":[opponent1, opponent2]}}}, 
        {"$project": {"teamname": 1, "stats_list": { "$filter":{"input":'$stats_list', 
            "cond":{"$eq":["$$this.games_through",datetime.datetime.strptime("2019-11-30","%Y-%m-%d")]}}}}}]
    test = mongo['stageprod_agg']['teststats'].aggregate(pipeline)
    lista_test = list(test)
    
    #names may cross at some point, so redefining here for labels later on
    try:
        new_team1=lista_test[0]['teamname']
        new_team2=lista_test[1]['teamname']
    except IndexError as e:
        print("error caught at list_test. Element 0 has the following keys: {}".format(lista_test[0].keys()))
    
    team1_li = lista_test[0]['stats_list']
    team2_li = lista_test[1]['stats_list'] # will return a dict element
    teamDataDict = {new_team1:team1_li,new_team2:team2_li}

#select the team w/the shortest list to compose the sorted_list; if not, may generate key value errors later... forsort is set to the df w/the fewest records... and so the order may be rearranged
    forsort = ((new_team1,team1_li),(new_team2,team2_li))[np.argmin((len(team1_li),len(team2_li)))]
    newSecondTeam = [i for i in teamDataDict.keys() if i != forsort[0]][0]
#extract the stat headers of the shortest df
#iterate two objects: 1) stats headers 2) stats dict for the team
    sorted_list = sorted([i['statlabel'] for i in forsort[1]])
    #iterate two objects: 1) stats headers 2) stats dict for the team
    tm1_sorted = [stat for i in sorted_list for stat in forsort[1] if stat['statlabel'] ==i]
#iterate two objects: 1) stats headers 2) stats dict for the team
    tm2_sorted = [stat for i in sorted_list for stat in     teamDataDict[newSecondTeam] if stat['statlabel'] ==i]
            
    return((forsort[0],newSecondTeam,tm1_sorted,tm2_sorted))
