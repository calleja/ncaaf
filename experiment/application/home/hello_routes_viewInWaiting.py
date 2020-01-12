@hello_bp.route('/rawResults2',methods='GET')
def rawStats2():
    #query the db w/results from selection above
    def extractToCSV(team1,team2):
        #will need to maintain as two separate DFs and project one onto each <div>
        ''' 
        1. query the database and extract team stats  a/o latest date
        2. separate each team into its own container
        3. sort the container so that team list matches same order
        4. measure the longest dict in ea container
        5. write each list of dicts to csv in format encoded
        '''
        pipeline = [{"$match":{'teamname':{"$in":[team1,team2]}}}, 
        {"$project": {"teamname": 1, "stats_list": { "$filter":{"input":'$stats_list', 
            "cond":{"$gte":["$$this.games_through",datetime.datetime.strptime("2019-10-19","%Y-%m-%d")]}}}}}]
        test = agg['teststats'].aggregate(pipeline)
        lista_test = list(test)
    
    #names may cross at some point, so redefining here for labels later on
        new_team1=lista_test[0]['teamname']
        new_team2=lista_test[1]['teamname']
    
        team1_li = lista_test[0]['stats_list']
        team2_li = lista_test[1]['stats_list'] # will return a dict element
    
    #select the team w/the shortest list to compose the sorted_list; if not, may generate key value errors later
        forsort = (team1_li,team2_li)[np.argmin((len(team1_li),len(team2_li)))]
        sorted_list = sorted([i['statlabel'] for i in forsort])
        tm1_sorted = [stat for i in sorted_list for stat in team1_li if stat['statlabel'] ==i]

    tm2_sorted = [stat for i in sorted_list for stat in team2_li if stat['statlabel'] ==i]
    
    max_dict = max([len(i) for i in tm2_sorted])*2 +1
    path = '/home/merde/Documents/ncaaf/matchups/'
    filename = team1 + '_' + team2 + '.csv'
    with open(path + filename, 'w') as file_temp:
        file_temp_writer=csv.writer(file_temp)
        for (a,b) in zip(tm1_sorted, tm2_sorted):
            temp_list_a = []
            temp_list_a.append(new_team1 + '-->')
            impute_no = max_dict - len(a)*2
            for k1,v1 in a.items():
                temp_list_a.append(k1)
                temp_list_a.append(v1)
        # enter spaces
            for i in range(impute_no):
                temp_list_a.append('')
        
            temp_list_a.append(new_team2 +'-->')
            for k2,v2 in b.items():
                temp_list_a.append(k2)
                temp_list_a.append(v2)
            file_temp_writer.writerow(temp_list_a)
