#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 21:27:38 2020

@author: merde
"""
import pymongo

client = pymongo.MongoClient(host='localhost',port=27017,serverSelectionTimeoutMS=maxSevSelDelay)
client.database_names()
#client.[database name]
db=client['voter_history']

client = pymongo.MongoClient(host = 'localhost', port = 27017)
client.list_database_names()
db = client['stageprod_agg']
teamlist = sorted(list(db['teststats'].distinct('teamname')))
    #convert list to a list of tuples... THIS NEEDS TO BE TESTED AGAIN
team_tups = [(i,val) for i, val in enumerate(teamlist,1)]
team_tups[0:8]
