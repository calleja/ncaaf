import pymongo
import numpy as np
import datetime
import json
import dateutil.parser
import dash
import sys
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import re
import pandas as pd

''' ideally will produce a graph off of just the url including the two teams; initially the data should be referenced upon db query, then later move on to retrieval from the hidden div or the dcc storage element'''
mongo = pymongo.MongoClient("mongodb+srv://luis-owner:persyy1981@cluster0-rpjy6.mongodb.net/stageprod_agg?retryWrites=true&w=majority")

#create a week calendar for the dropdown.. still in dev using robomongo
dates = mongo['stageprod_agg']['teststats'].aggregate([{'$unwind':"$stats_list"},{'$group':{'_id':"$stats_list.games_through"}},{'$sort':{'_id':1}}])

lista_test = list(dates)
#define the dict storing all dates/weeks for dropdown
dates_dict = [{'label':'week '+str(counter+1),'value':value['_id']} for counter, value in enumerate(lista_test)]
#print(f'dates_dict is composed of {dates_dict}')
real_dates_dict = {i['label']:i['value'] for i in dates_dict}
#print(f'real_dates_dict is composed of {real_dates_dict}')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()
    
def controller(server):
    dash_app = dash.Dash(__name__,
                         server=server,
                         routes_pathname_prefix='/dashapp/',
                         external_stylesheets=['/static/css/styles.css'])
    dash_app.config.suppress_callback_exceptions = True
    dash_app.layout = html.Div(children=[
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='dataset', storage_type='local'),
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''), dcc.Dropdown(id='week_list', options = dates_dict),             
#candidate object though which to render new plots
    html.Div([],id='my-output'),
    html.Div([],id='my-outputII'),
    #hidden DIV for persistance of result set
    html.Div(id='mongo_list', style={'display': 'none'})])
    ''' Initial query must be done w/in a callback context bc that context is necessary to receive the team names... ideally the user would be served up the latest week's results by default, and then have a dropdown from which they can choose earlier weeks'''    
    #Output is a dcc object
    init_callbacks(dash_app)
    return dash_app.server

def init_callbacks(dash_app):
    '''PASS THE DASH APP TO A FUNCT THAT ENCAPSULATES ALL THE CALLBACKS AND PLACE "return dash_app.server" in the controller function'''
    @dash_app.callback([Output(component_id='my-output', component_property='children'), Output('mongo_list','children'), Output('dataset','data')], [Input('url', 'href'), Input('week_list', 'value')],[State('dataset','data')])
    #three outputs: 1) default graph; 2) json into hidden div; 3) dcc data store object
    def create_dashboard(href,value,data):
        #split the url to extract the team names
        #will now make a direct call to extractToCSV which returns the raw dataset of all year's data for both teams; this is subsequently stored in the client's browser; later in this callback, we apply compileData() to clean the raw data for the date/game week parameters we select
        if value != None:
            children = [None]
            return children, data, data
        else:
            try:
                print(f"the calling URL into dash is {href}")
                lista = href.split("/")
                p = re.compile('%20')
                lista = [p.sub(' ',i) for i in lista]
            #parse the href for the two opps
                opp1,opp2 = list(filter(None, lista))[-2:]
            #access point to rest of app
            # will now come from a new call to compileData that DOESN'T subsequently call extractToCSV()
            #fullDataset is a list of len 2; ea elem is a dict of two keys = '_id' (teamname) & 'stats_date'; stats_date is a list of size coinciding w/#of weeks recorded; ea elem of stats_date is a dict having 2 keys: 'games_through' (a datetime: YYY-mm-dd 00:00:00) and 'entry' - a list of all ~44 stats in the form of their own dict... to summarize: list -> elem['stats_date'] -> list -> elem['entry'] -> list -> dict of stats for the week in question
                teamName1, teamName2, fullDataset = extractToCSV(opp1,opp2)
                def myconverter(o):
    #json encoder supporting function; converts dates to strings
                    if isinstance(o, datetime.datetime):
                        return o.__str__()
    
        #json/str object; will be unpacked in compileData()
                jtest = json.dumps(fullDataset, default = myconverter)
        
        #make call to the new version of compileData(), which is expected to unserialize the json
                opponent1_cd,opponent2_cd, df_opponents = compileData(fullDataset = jtest)
            except (IndexError, AttributeError) as e:
                print(e)
                sys.exit(1)
            #teamName1, teamName2, fullDataset = extractToCSV('Rutgers','Florida')

        #returned object from extractToCSV: the full result set and store client-side in hidden div
        
        
            try:
        #graphing framework once variables are declared
                data = [go.Bar(x=df_opponents['rank1'], y=df_opponents.index, name=opponent1_cd+ ' Ranks', orientation = "h", text = df_opponents['rank1'], textposition = 'outside'), go.Bar(x=df_opponents['rank2'], y=df_opponents.index, name=opponent2_cd+' Ranks', orientation = "h", text = abs(df_opponents['rank2']), textposition = 'outside')]
                     
                layout = go.Layout(barmode='overlay', height = None, title = go.layout.Title(text="Side-by-side rankings"), margin=dict(l = 200), xaxis = dict(tickmode = 'array', tickvals = [-100,-75,-50,-25,0, 25, 50, 75, 100],ticktext = ['100', '75','50','25','0','25', '50', '75', '100'] ) )
                fig = go.Figure(dict(data = data, layout = layout))
                children = []
                children.append(dcc.Graph(figure = fig))
                return children, jtest, jtest
            except TypeError as e:
                print("encountered an error in graphing portion of first callback. The objects in question are df_opponents of class {}, and dim: {}, df_opponents.index of length {}, opponent1_cd: {} and opponent2_cd: {}".format(str(type(df_opponents)), str(df_opponents.shape), len(df_opponents.index), opponent1_cd, opponent2_cd))

    @dash_app.callback([Output(component_id='my-outputII', component_property='children')], [Input('week_list', 'value'),Input('dataset','data')])
    #second callback for week-specific interaction
    def dropdownInteraction(value, data):
        #if dropdown is not selected, hide the div
        if value == None:
            children = [None]
            return children
        else:
            print(f'running compileData from 2nd callback on value {value} from the dropdown, which is of type {type(value)}')
            opponent1,opponent2, df_opponents = compileData(wkOfAction = value, fullDataset = data)
        
            data = [go.Bar(x=df_opponents['rank1'], y=df_opponents.index, name=opponent1+ ' Ranks', orientation = "h", text = df_opponents['rank1'], textposition = 'outside'), go.Bar(x=df_opponents['rank2'], y=df_opponents.index, name=opponent2+' Ranks', orientation = "h", text = abs(df_opponents['rank2']), textposition = 'outside')]
                     
            layout = go.Layout(barmode='overlay', height = None, title = go.layout.Title(text="Side-by-side rankings"), margin=dict(l = 200), xaxis = dict(tickmode = 'array', tickvals = [-100,-75,-50,-25,0, 25, 50, 75, 100],ticktext = ['100', '75','50','25','0','25', '50', '75', '100'] ) )
            fig = go.Figure(dict(data = data, layout = layout))
            children = []
            children.append(dcc.Graph(figure = fig))
            return children
    

def compileData(wkOfAction = 'latest', fullDataset = None):
    #leave this as an independent/unafilliated funct
    #oft-called funct that will accept the two opponents and the date of action (or the default)
    #if fullDataset is not passed, this funct should retrieve it from the hidden div; possible bc funct is outside of any callback context
    if wkOfAction == 'latest':
        #index from the bottom of the list
        wkOfAction = dates_dict[-1]['value']
    else:
        #print(f"from compileData(); wkOfAction is {wkOfAction}, which is of type {type(wkOfAction)}")
        wkOfAction = datetime.datetime.strptime(wkOfAction,"%Y-%m-%dT%H:%M:%S")
        
        #print(f'real dates dict is {real_dates_dict}')
        #print(f"but this works {dates_dict[-1]['value']}, which is of type {type(dates_dict[-1]['value'])}")
        
        
    #fullDataset is a list of dicts of a list of dicts; a json serialized dataset from extractToCSV
    #load the dataset stored w/in the hidden div
    def DecodeDateTime(topLevelList):
        storeBoth = []
        for teamHiDict in topLevelList:
            for game_wk in teamHiDict['stats_date']:
                    game_wk['games_through'] = dateutil.parser.parse(game_wk['games_through'])
                    for stat_level in game_wk['entry']:
                        stat_level['games_through'] = dateutil.parser.parse(stat_level['games_through'])
            storeBoth.append(teamHiDict)
        return storeBoth
    #fullDataset is always passed in the compileData() call, and is always serialized, hence, the need to load below
    gh = json.loads(fullDataset) # a list of two elems: one per team     
#contains all stats on every week for both teams in the form of a dict w/keys '_id' (contains team name) and 'stats_date' - a list of dicts, themselves containing keys 'entry' and 'games_through', which is a datetime object
    fullds = DecodeDateTime(gh)
    #traverse the body of objects in one line (once for ea team)    
#select for the relevant game week of stats from ea team - default is latest week; teamN_li is a list of one element: a collection of dicts of ea stat collected for that week    
    try:
        team1_li = [dic['entry'] for dic in fullds[0]   ['stats_date'] if dic['games_through'] ==  wkOfAction]
        #datetime.datetime.strptime("2019-11-30","%Y-%m-%d")]
    #replace above w/date_dict value
        new_team1 = fullds[0]['_id']
        new_team2 = fullds[1]['_id']
        team2_li = [dic['entry'] for dic in fullds[1]['stats_date'] if dic['games_through'] == wkOfAction]
        teamDataDict = {new_team1:team1_li,new_team2:team2_li}
    except KeyError:
        print("There was a key error. The value of wkOfAction is {}".format(str(wkOfAction)))

    #select the team w/the shortest list to compose the sorted_list; if not, may generate key value errors later... forsort is set to the df w/the fewest records... and so the order may be rearranged

    #extract the stat headers of the shortest df
    forsort = ((new_team1,team1_li),(new_team2,team2_li))[np.argmin((len(team1_li[0]),len(team2_li[0])))]
#teamname
    newSecondTeam = [i for i in teamDataDict.keys() if i != forsort[0]][0]

#iterate two objects: 1) stats headers 
#this list is in the order of y-axis I'd like to display
    sorted_list = sorted([i['statlabel'] for i in forsort[1][0]])

#now that the order of the stats has been arranged, apply to EACH team's dataset
#list of dicts that adheres to order of sorted_list
    tm1_sorted = [stat for i in sorted_list for stat in     forsort[1][0] if stat['statlabel'] ==i]
    tm2_sorted = [stat for i in sorted_list for stat in     teamDataDict[newSecondTeam][0] if stat['statlabel'] ==i]

    #return(forsort[0],newSecondTeam,tm1_sorted,tm2_sorted)
    df = convertToDF(tm1_sorted,tm2_sorted)
    print(f'The df output by compile data for teams {forsort[0]} and {newSecondTeam} for the week of {wkOfAction} is {df}')
    return(forsort[0], newSecondTeam, df)
    
    
def convertToDF(ncaa_rank_coll_team1,ncaa_rank_coll_team2):
    # KIM team name is not stored in the argument objects
    def extract(dic):
        return [k for g,k in dic.items() if g in ['statlabel','Rank']]
    
    team1 = [extract(k) for k in ncaa_rank_coll_team1]
    team2 = [extract(k) for k in ncaa_rank_coll_team2]
    df1 = pd.DataFrame(team1, columns = ['statlabel','rank1'])
    df2 = pd.DataFrame(team2, columns = ['statlabel','rank2'])
    
    #Concatenate the two separate team dataframes into one, and allow the rogue stat with a counterpart in each dataframe to dangle.
    #set the row indexes equal to the statlabel so I can concatenate properly
    df1.set_index('statlabel', inplace = True)
    df2.set_index('statlabel', inplace = True)
    
    df = pd.concat([df1,df2], axis = 1)
    df['diff'] = abs(df['rank2'] - df['rank1'])
    df['rank2'] = df['rank2'] * -1

    #add a categorical variable for the size of the discrepancy between rankings; 
    #this variable will be used later to highlight bars on the barchart
    cut_bins=[0,60,100]
    cut_labels = ['normal','pronounced']
    df['rank_disp'] = pd.cut(df['diff'], bins=cut_bins,     labels=cut_labels)
    #return(forsort[0],newSecondTeam,tm1_sorted,tm2_sorted)
    return(df)
    

def extractToCSV(opponent1, opponent2):
    '''in this version, I will pull down all the stats for the teams across game weeks'''
    pipeline = ([{"$match":{'teamname':{"$in":[opponent1, opponent2]}}}, 
        {"$unwind":'$stats_list'}, 
        {"$group":{"_id": {"teamname":"$teamname","games_through":"$stats_list.games_through"}, 
        "entry": {"$push":'$stats_list'}}},
        {"$group":{"_id": "$_id.teamname", "stats_date": {"$push":{"games_through":"$_id.games_through", 
        "entry": '$entry'}}}}])
    #should return two lists containing 44* (# of weeks) of sublists... and ea of those contain 9 elems
    test = mongo['stageprod_agg']['teststats'].aggregate(pipeline)

#list composed of one dict for each team: key = teamname; value = list of stats for ea week of action in the form of a dictionary having a key of date of action and a value of a list composed of ea stat category... dict->list->dict->list
    lista_test = list(test)
#names may cross at some point, so redefining here for labels later on
    try:
        new_team1=lista_test[0]["_id"]
        new_team2=lista_test[1]["_id"]
    except IndexError as e:
        print("error caught at list_test. Element 0 has the following keys: {}".format(lista_test[0].keys()))
    #context is crucial here... ea user's session must have defined unique object values... one solution is to tuck all the functions into the callback, but I can assume other callbacks to be developed in the future
    
    return(new_team1,new_team2, lista_test)
#may need to isolate the quant stats portion as well... not by the week, the whole dataset... this data will need to be saved at a high scope so that subsequent callbacks may access
