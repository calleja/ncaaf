
""" The below is a branch offshoot of 'dropdownAppContruction...TESTING_callbackFunct.py'  OBJECTIVE: to fix the forsort feature in compileData()... this code doesn't require any server; it is serverless. Try to complete execution without tripping up IndexError (out of range): forsort = ((new_team1,team1_li),(new_team2,team2_li))[np.argmin((len(team1_li[0]),len(team2_li[0])))]
IndexError: list index out of range """

import pymongo
import numpy as np
import datetime
import json
import dateutil.parser
import pandas as pd

mongo = pymongo.MongoClient("mongodb+srv://luis-owner:persyy1981@cluster0-rpjy6.mongodb.net/stageprod_agg?retryWrites=true&w=majority")

#create a week calendar for the dropdown.. still in dev using robomongo
dates = mongo['stageprod_agg']['teststats'].aggregate([{'$unwind':"$stats_list"},{'$group':{'_id':"$stats_list.games_through"}},{'$sort':{'_id':1}}])

lista_test = list(dates)
#define the dict storing all dates/weeks for dropdown
dates_dict = [{'label':'week '+str(counter+1),'value':value['_id']} for counter, value in enumerate(lista_test)]

real_dates_dict = {i['label']:i['value'] for i in dates_dict}
wkOfAction = "week 5"
wkOfAction = real_dates_dict.get(wkOfAction,dates_dict[-1]['value'])

def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


teamName1, teamName2, fullDataset = extractToCSV('Rutgers','Florida')


#json/str object; will be unpacked in compileData()
jtest = json.dumps(fullDataset, default = myconverter)

opponent1_cd,opponent2_cd, df_opponents = compileData(fullDataset = jtest)

df = convertToDF(df_opponents[0],df_opponents[1])


def compileData(wkOfAction = 'latest', fullDataset = None):
    #leave this as an independent/unafilliated funct
    #oft-called funct that will accept the two opponents and the date of action (or the default)
    #if fullDataset is not passed, this funct should retrieve it from the hidden div; possible bc funct is outside of any callback context
    if wkOfAction == 'latest':
        #index from the bottom of the list
        wkOfAction = dates_dict[-1]['value']
    else:
        print("wkOfAction is {}".format(str(wkOfAction)))
        
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
        print("The value of wkOfAction is {}".format(str(wkOfAction)))

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
    df = [tm1_sorted,tm2_sorted]
    return(forsort[0], newSecondTeam, df)


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