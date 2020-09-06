import pymongo
import numpy as np
import datetime
import json
import dateutil.parser
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output

'''The below program incorporates 'basicBuildEvolvedII.py' and 'pymongoWork_nested.py' to deliver an app of default graphs and interactive weekly graphs. This dash app relies on a flask server; notice the controller() accepts a server argument'''
'''Program should
1. accept two team names
2. query the mongoDB and store/retrieve the full year's dataset (but not unpack or parse) 
3. store a map of week timestamp to week number for drop-down purposes
4. select, parse the larger dataset by week timestamp
5. charting
'''
mongo = pymongo.MongoClient("mongodb+srv://luis-owner:persyy1981@cluster0-rpjy6.mongodb.net/stageprod_agg?retryWrites=true&w=majority")

#create a week calendar for the dropdown.. still in dev using robomongo
dates = mongo['stageprod_agg']['teststats'].aggregate([{'$unwind':"$stats_list"},{'$group':{'_id':"$stats_list.games_through"}},{'$sort':{'_id':1}}])

lista_test = list(dates)
#define the dict storing all dates/weeks for dropdown
dates_dict = [{'label':'week '+str(counter+1),'value':value['_id']} for counter, value in enumerate(lista_test)]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()
    
def controller(server):
    dash_app = dash.Dash(__name__,
                         server=server,
                         routes_pathname_prefix='/',
                         external_stylesheets=['/static/css/styles.css'])
    
    dash_app.layout = html.Div(children=[
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='dataset', storage_type='local'),
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''), dcc.Dropdown(id='week_list', options = dates_dict),             
#candidate object though which to render new plots
    dcc.Graph(
        id='my-output'),
    #hidden DIV for persistance of result set
    html.Div(id='mongo_list', style={'display': 'none'})])
    
    ''' Initial query must be done w/in a callback context bc that context is necessary to receive the team names... ideally the user would be served up the latest week's results by default, and then have a dropdown from which they can choose earlier weeks'''    
#Output is a dcc object
    @dash_app.callback([Output(component_id='my-output', component_property='figure'), Output('mongo_list','children'), Output('dataset','data')], [Input('url', 'href')])
    #three outputs: 1) default graph; 2) json into hidden div; 3) dcc data store object
    def create_dashboard(href):
        #split the url to extract the team names
        #will now make a direct call to extractToCSV which returns the raw dataset of all year's data for both teams; this is subsequently stored in the client's browser; later in this callback, we apply compileData() to clean the raw data for the date parameters we select
        try:
            lista = href.split("/")
            #parse the href for the two opps
            opp1,opp2 = list(filter(None, lista))[-2:]
            #access point to rest of app
            # will now come from a new call to compileData that DOESN'T subsequently call extractToCSV()
            teamName1, teamName2, fullDataset = extractToCSV(opp1,opp2)
        except (IndexError, AttributeError) as e:
            teamName1, teamName2, fullDataset = extractToCSV('Rutgers','Florida')

        #returned object from extractToCSV: the full result set and store client-side in hidden div
        def myconverter(o):
    #json encoder supporting function; converts dates to strings
            if isinstance(o, datetime.datetime):
                return o.__str__()
    
        #json/str object; will be unpacked in compileData()
        jtest = json.dumps(fullDataset, default = myconverter)
        
        #make call to the new version of compileData(), which is expected to unserialize the json
        opponent1,opponent2, df_opponents = compileData(fullDataset = jtest)
        
        #graphing framework once variables are declared
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
        return fig, jtest, jtest
    return dash_app.server

    @dash_app.callback([Output(component_id='my-output', component_property='figure')], [Input('week_list', 'value'),Input('dataset','data')])
    #second callback for week-specific interaction
    def dropdownInteraction(value, data):
        opponent1,opponent2, df_opponents = compileData(wkOfAction = value)
        
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

def compileData(wkOfAction = 'latest', fullDataset = None):
    #leave this as an independent/unafilliated funct
    #oft-called funct that will accept the two opponents and the date of action (or the default)
    #if fullDataset is not passed, this funct should retrieve it from the hidden div; possible bc funct is outside of any callback context
    if wkOfAction == 'latest':
        wkOfAction = dates_dict[0]['value']
        
    def extract(dic):
        return [k for g,k in dic.items() if g in ['statlabel','Rank']]
    #fullDataset is a list of dicts of a list of dicts; a json serialized dataset from extractToCSV
    #load the dataset stored w/in the hidden div
    def DecodeDateTime(topLevelList):
        for teamHiDict in topLevelList:
            for game_wk in teamHiDict['stats_date']:
                    game_wk['games_through'] = dateutil.parser.parse(game_wk['games_through'])
                    for stat_level in game_wk['entry']:
                        stat_level['games_through'] = dateutil.parser.parse(stat_level['games_through'])
        return teamHiDict    
    gh = json.loads(fullDataset) # a list of two elems: one per team     
#contains all stats on every week
    fullds = DecodeDateTime(gh)
    
    #traverse the body of objects in one line (once for ea team)    
#select for the relevant game week of stats from ea team - default is latest week; teamN_li is a list of one element: a collection of dicts of ea stat collected for that week    
    team1_li = [dic['entry'] for dic in fullds[0]   ['stats_date'] if dic['games_through'] ==  wkOfAction]
    new_team1 = fullds[0]['_id']
    new_team2 = fullds[1]['_id']
    try:
        team2_li = [dic['entry'] for dic in fullds[1]['stats_date'] if dic['games_through'] == wkOfAction]
        teamDataDict = {new_team1:team1_li,new_team2:team2_li}
    except KeyError:
        print("The value of wkOfAction is {}".format(str(wkOfAction))

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

#if a funct is composed, may need to mimic this as the returned value
    return(forsort[0],newSecondTeam,tm1_sorted,tm2_sorted)

            
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

