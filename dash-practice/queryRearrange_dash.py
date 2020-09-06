#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 20:29:22 2020

@author: merde
"""
import pymongo
import numpy as np
import datetime
import pandas as pd
from datetime import datetime

mongo = pymongo.MongoClient("mongodb://localhost:27017/stageprod_agg")

def fullDateRangeExtract(opponent1, opponent2):
    pipeline = [{"$match":{'teamname':{"$in":[opponent1, opponent2]}}}, 
        {"$project": {"teamname": 1, "stats_list": '$stats_list'            }}]
    #should return two lists containing 44* (# of weeks) of sublists... and ea of those contain 9 elems
    test = mongo['stageprod_agg']['teststats'].aggregate(pipeline)
    
    lista_test = list(test)
    #names may cross at some point, so redefining here for labels later on
    try:
        new_team1=lista_test[0]['teamname']
        new_team2=lista_test[1]['teamname']
    except IndexError as e:
        print("error caught at list_test. Element 0 has the following keys: {}".format(lista_test[1].keys()))
    
    try:
        team1_li = lista_test[0]['stats_list']
        team2_li = lista_test[1]['stats_list'] # will return a dict element
    except IndexError as e:
        print("keys in lista_test[1]: {}".format(lista_test[1].keys()))
    
    teamDataDict = {new_team1:team1_li,new_team2:team2_li}
    return(teamDataDict,new_team1,new_team2)
    
teamLists,teamname1, teamname2 = fullDateRangeExtract('Clemson','Alabama')   

df_clem = pd.DataFrame(test['Clemson'])
df_clem.columns

def (dictofLists,teamname1,teamname2,week):
    #this function will query the two dataframes on the week of activity, then sort and index according to shared stats
    #select the team w/the shortest list to compose the sorted_list; if not, may generate key value errors later... forsort is set to the df w/the fewest records... and so the order may be rearranged
    forsort = ((teamname1,dictofLists[teamname1]),(teamname2,dictofLists[teamname2]))[np.argmin((len(dictofLists[teamname1]),len(dictofLists[teamname2])))]
    newSecondTeam = [i for i in teamDataDict.keys() if i != forsort[0]][0]
#extract the stat headers of the shortest df
#iterate two objects: 1) stats headers 2) stats dict for the team
    sorted_list = sorted([i['statlabel'] for i in forsort[1]])
    #iterate two objects: 1) stats headers 2) stats dict for the team
    tm1_sorted = [stat for i in sorted_list for stat in forsort[1] if stat['statlabel'] ==i]
#iterate two objects: 1) stats headers 2) stats dict for the team
    tm2_sorted = [stat for i in sorted_list for stat in     teamDataDict[newSecondTeam] if stat['statlabel'] ==i]
            
    return((forsort[0],newSecondTeam,tm1_sorted,tm2_sorted))