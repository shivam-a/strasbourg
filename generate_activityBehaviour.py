# -*- coding: utf-8 -*-
"""
Created on Fri May 25 13:52:05 2018

@author: slehmler
"""
import pandas as pd
import numpy as np
import configparser

config = configparser.ConfigParser()
config.read("CONFIG.txt")
aoi = [c for c in config["basic information"]["areas of interest"].split(',')]
def get_activity_behaviour():
    method = config["activity behaviour"]["method"]
    if method == "emd":
        return _emd()

def _prepare_emd():
    #rename EMD-variables (just to make data more understandable)
    #dictionary for renaming deplacements
    deplacement_variables = {
        "SECT1": "sector",
        "SECT2": "sector_fine",
        "ECH": "sample_id",
        "NUMPERS": "person_id",
        "NUMDEP": "deplacement_id",
        "D2A": "origin_motive",
        "D3": "origin_zone",
        "D4A": "depart_hour",
        "D4B": "depart_minute",
        "D5A": "destination_motive",
        "D7": "destination_zone",
        "D8A": "arrival_hour",
        "D8B": "arrival_minute",
        }
    #dictionary for renaming people variables
    people_variables ={
        "SECT1": "sector",
        "SECT2": "sector_fine",
        "ECH": "sample_id",
        "NUMPERS": "person_id", 
        "Coef": "coefficient",
        "P4" : "age"
        }
    #dictionary for renaming motives
    #EMD defines some ordered number code to different activities
    #this is used to group activities into categories
    #here: only home, work, study, shopping, leisure, other
    def rename_motive(cell):
        value = int(cell)
        if value <10:
            return "Home"
        elif value < 20:
            return "Work"
        elif value < 29:
            return "School"
        elif value < 30:
            return "University"
        elif value < 40:
            return "Shopping"
        elif value > 50 and value < 60:
            return "Leisure"
        elif value < 70:
            return "Accompany"
        else:
            return "Other"
    #dictionary for renaming age(creating age groups)
    #at the moment, it uses the grouping from the census
    def rename_age(cell):
        value = int(cell)
        if value <= 14:
            return "00_14"
        elif value <= 29:
            return "15_29"
        elif value <= 44:
            return "30_44"
        elif value <= 59:
            return "45_59"
        elif value <= 74:
            return "60_74"
        else:
            return "75_"
#    def rename_age(cell):
#        value = int(cell)
#        if value <= 10:
#            return "05_10"
#        elif value <= 19:
#            return "11_19"
#        elif value <= 59:
#            return "20_59"
#        elif value <= 74:
#            return "60_74"
#        else:
#            return "75_99"
#    iris_zonefine = "X:\\Projects\\OnGoing\\P11GD\\WP04 CityMob\\04_SNCF\\1_data\\shape\\iris_zf_RJ.xls"
#    matching_df = pd.read_excel(iris_zonefine, sheet_name = 1)
#
#    def zf_to_iris(row):
#        iris = matching_df[matching_df["Id_zf_cere"] == int(row.D3)].CODE_IRIS.values
#        if iris.any():
#            d3 = str(iris[0])
#        else:
#            d3 = ""
#        iris = matching_df[matching_df["Id_zf_cere"] == int(row.D7)].CODE_IRIS.values
#        if iris.any():
#            d7 = str(iris[0])
#        else:
#            d7 = ""
#        return d3,d7

    #read deplacement.csv (from EMD)
    #only keep the variables of interest and rename them
    deplacements = pd.read_csv(config["inputfiles"]["survey folder"]+"DEPLACEMENTS.csv",sep=";", dtype=str )
    #deplacements[["D3", "D7"]] = deplacements.apply(zf_to_iris,axis=1, result_type="expand")
    
    #split time
    deplacements["D4A"] = deplacements.D4.str.extract("(\d\d)\d\d")
    deplacements["D4B"] = deplacements.D4.str.extract("\d\d(\d\d)")
    deplacements["D8A"] = deplacements.D8.str.extract("(\d\d)\d\d")
    deplacements["D8B"] = deplacements.D8.str.extract("\d\d(\d\d)")
    
    deplacements = deplacements[list(deplacement_variables.keys())]
    deplacements = deplacements.dropna()
    
    deplacements = deplacements.rename(columns = deplacement_variables)
    #rename origin and destination motives
    deplacements.origin_motive = deplacements.origin_motive.apply(rename_motive)
    deplacements.destination_motive = deplacements.destination_motive.apply(rename_motive)
    
    #read people.csv (from EMD)
    #only keep the variables of interest and rename them
    people = pd.read_csv(config["inputfiles"]["survey folder"]+"PERSONNES.csv", sep=";", dtype=str)
    people = people[list(people_variables.keys())]
    people = people.rename(columns = people_variables)
    people = people.dropna()
    #age-grouping
    people.age = people.age.apply(rename_age)
    
    #merge deplacements and people
    return pd.merge(deplacements, people, on = ["sector", "sector_fine", "person_id","sample_id"], how = 'left' )

def _emd():    
    #define the function (to be called later) that is used on each person df 
    #with the aim to create this persons (home-based) tours
    #return something like:
    #person_id|work|study|shopping|leisure|other | nb_tours | age_group
    #   x     |  1 |  1  |  0     |  1    |   0  |  3       | ...
    #
    #TODO:
    #change activities (split study in school & university, add accompany ?)
    def get_tour_dis(person_df):
        #ignore every person in the survey, not starting or ending at home (not part of our population) ?
        if (person_df.origin_motive.values[0] != "Home") or (person_df.iloc[-1:].destination_motive.values != "Home"):
            return None
        
        #create a string describing the tours of one person
        #looks like:
        #home>study>home>shopping>leisure>home
        tours = ">".join(np.append(person_df.origin_motive.values, person_df.iloc[-1:].destination_motive.values))
        #and split the string at ">home>" to get a list with the home based trips
        #looks like:
        # ["home>study", "shopping>leisure>home"]
        tours = tours.split(">Home>")
        #not sure that this is the most efficient way to do things...
        #TODO:
        #evaluate other ways
        
        #we now iterate the list of home-based tours and count the main activity
        #according to the hierarchy that Jordan used
        tour_dict = {"Work": 0, "School": 0, "University": 0, "Shopping": 0, "Leisure": 0, "Accompany": 0, "Other":0 }
        for tour in tours:
            if "Work" in tour:
                tour_dict["Work"] +=1
            elif "School" in tour:
                tour_dict["School"] +=1
            elif "University" in tour:
                tour_dict["University"] +=1
            elif "Shopping" in tour:
                tour_dict["Shopping"] +=1
            elif "Leisure" in tour:
                tour_dict["Leisure"] +=1
            elif "Accompany" in tour:
                tour_dict["Accompany"] +=1
            else:
                tour_dict["Other"] +=1
        #add age group and number of tours taken
        #then return a panda series
        tour_dict["age_group"] = person_df.age.unique()[0]
        tour_dict["nb_tours"] = len(tours)
        return pd.Series(tour_dict)
    
    def removeOutlier(row):
        l = [x in aoi for x in np.append(row.origin_zone.values, row.destination_zone.values)]
        if all(l):
            return row
        
    
    depl_peopl = _prepare_emd()
    #depl_peopl = depl_peopl.groupby(["sector","sector_fine", "sample_id", "person_id"]).apply(removeOutlier)
    #group by person in EMD
    #and apply aboves function (get_tour_dis) to every person in the sample
    #the result looks like this:
    #person_id|work|study|shopping|leisure|other | nb_tours | age_group
    #   x1     |  1 |  1  |  0     |  1    |   0  |  3       | ...
    #   x2     |  1 |  0  |  0     |  0    |   0  |  1       | ...
    person_tours = depl_peopl.groupby(["sector","sector_fine", "sample_id", "person_id"]).apply(get_tour_dis)
    #TODO:
    #every Person comes with an weight-coefficient in the EMD
    #this coefficient it ignored for now
    #maybe it makes sense to multiply each person according to it coefficient
    
    #group by age_group and calculate the sum
    #work|study|shopping|leisure|other | nb_tours | age_group
    # 150| 68  |  50    |  102  |  30  |  400       | group1
    # 200|  200|  0     |  50   |   0  |  450       | group2
    person_tours_dis = person_tours.groupby(["age_group"]).sum()
    #divide by number of tours to get ratio
    #TODO:
    #change activities
    dis = person_tours_dis[["Work","School","University","Shopping","Leisure","Accompany","Other"]].div(person_tours_dis["nb_tours"], axis = 0)
    #dis["average_nb_tours"] = person_tours_dis["nb_tours"] / person_tours.groupby(["age_group"]).size()
    return dis[["Work","School","University","Shopping","Leisure","Accompany","Other"]]

def mean_trip_length(mean=False):
    ''' this is not needed for PRIME'''

    def get_trip_length(person_df, mean=False):
        def calc_time(activity, mean=False):
            starting_time = re.findall('\d+:\d+', tour)[0]
            starting_time = datetime.datetime.strptime(starting_time, '%H:%M')
            arrival_time = re.findall(activity+'\|(\d+:\d+)', tour)[0]
            arrival_time = datetime.datetime.strptime(arrival_time, '%H:%M')
            if mean:
                final_time = re.findall('\d+:\d+', tour)[-1]
                final_time = datetime.datetime.strptime(final_time, '%H:%M')
                departure_time = re.findall(activity+'\|\d+:\d+>(\d+:\d+)', tour)[0]
                departure_time = datetime.datetime.strptime(departure_time, '%H:%M')
                return (((final_time - departure_time).seconds + (arrival_time - starting_time).seconds)/2 )// 60
            else:
                return (arrival_time - starting_time).seconds // 60
        #ignore every person in the survey, not starting or ending at home (not part of our population) ?
        if (person_df.origin_motive.values[0] != "Home") or (person_df.iloc[-1:].destination_motive.values != "Home"):
            return None
        import re 
        import datetime
        #create a string describing the tours of one person
        #tours = ">".join(list(zip(person_df.origin_motif_time.values, person_df.destination_motif_time.values)))
        tours = ">".join(person_df.time_motif_time.values)
        tours = re.sub(r"(>\d+:\d+\|Home\|\d+:\d+>)", r'\1*', tours)
        res = re.split(r"\*", tours)
        #res = re.split(r">\d+:\d+\|Home\|\d+:\d+>", tours)
        
        time_dict = {"Work": 0, "School": 0, "University": 0, "Shopping": 0, "Leisure": 0, "Accompany": 0, "Other":0 }
        for tour in res:
            if tour:
                if "Work" in tour:
                    time_dict["Work"] = calc_time("Work", mean)
                elif "School" in tour:
                    time_dict["School"] = calc_time("School", mean)
                elif "University" in tour:
                    time_dict["University"] = calc_time("University", mean)
                elif "Shopping" in tour:
                    time_dict["Shopping"] = calc_time("Shopping", mean)
                elif "Leisure" in tour:
                    time_dict["Leisure"] = calc_time("Leisure", mean)
                elif "Accompany" in tour:
                    time_dict["Accompany"] = calc_time("Accompany", mean)
                elif "Other" in tour:
                    time_dict["Other"] = calc_time("Other", mean)
                else:
                    continue
        return pd.Series(time_dict)

        
    def removeOutlier(row):
        l = [x in aoi for x in np.append(row.origin_zone.values, row.destination_zone.values)]
        if all(l):
            return row
        
    
    depl_peopl = _prepare_emd()
    #depl_peopl = depl_peopl.groupby(["sector","sector_fine", "sample_id", "person_id"]).apply(removeOutlier)
    #some entries contain hours 24, 25, 26...
    #transform to values between 0 and 23
    depl_peopl.depart_hour = pd.to_numeric(depl_peopl.depart_hour) % 24
    depl_peopl.depart_hour = depl_peopl.depart_hour.astype(str)
    depl_peopl.arrival_hour = pd.to_numeric(depl_peopl.arrival_hour) % 24
    depl_peopl.arrival_hour = depl_peopl.arrival_hour.astype(str)
    
    depl_peopl["depart_time"] = depl_peopl.depart_hour + ":" +depl_peopl.depart_minute
    depl_peopl["arrival_time"] = depl_peopl.arrival_hour + ":" +depl_peopl.arrival_minute
    #depl_peopl["origin_motif_time"] = depl_peopl.origin_motive + "|" + depl_peopl.depart_time
    #depl_peopl["destination_motif_time"] = depl_peopl.destination_motive + "|" + depl_peopl.arrival_time
    depl_peopl["time_motif_time"] =depl_peopl.depart_time + "|" + depl_peopl.destination_motive + "|" + depl_peopl.arrival_time
    #return depl_peopl
    time_df = depl_peopl.groupby(["sector","sector_fine", "sample_id", "person_id"]).apply(get_trip_length, mean)
#    time_df = time_df.fillna(0)
#    #print(time_df.mean)
#    result = {}
#    for column in time_df:
#        result[column] = time_df.iloc[time_df[column].nonzero()[0]][column].values
    time_df = time_df.replace(0, np.NaN)
    
    return time_df.mean()

def activity_duration():

    def get_activity_duration(person_df):
        #ignore every person in the survey, not starting or ending at home (not part of our population) ?
        if (person_df.origin_motive.values[0] != "Home") or (person_df.iloc[-1:].destination_motive.values != "Home"):
            return None
        import re 
        import datetime
        #create a string describing the tours of one person
        #tours = ">".join(list(zip(person_df.origin_motif_time.values, person_df.destination_motif_time.values)))
        tours = ">".join(person_df.time_motif_time.values)
#        res = re.split(r">\d+:\d+\|Home\|\d+:\d+>", tours)
#        print(res)
        regex = r"(\w*)\|(\d\d:\d+)>(\d\d:\d+)"
        duration_dict = {"Home": 0, "Work": 0, "School": 0, "University": 0, "Shopping": 0, "Leisure": 0, "Accompany": 0, "Other":0 }
        
        for tup in re.findall(regex, tours):
#            if tup[0] != "Home":
            arrival = datetime.datetime.strptime(tup[1], '%H:%M')
            departure = datetime.datetime.strptime(tup[2], '%H:%M')
            duration_dict[tup[0]] = (departure - arrival).seconds // 60
        return pd.Series(duration_dict)
    
    def get_HomeBased_activity_duration(person_df):
        def calc_duration(activity):
            arrival_time = re.findall(activity+'\|(\d+:\d+)', tour)[0]
            arrival_time = datetime.datetime.strptime(arrival_time, '%H:%M')
            departure_time = re.findall('\|\d+:\d+>(\d+:\d+)', tour)[-1]
            departure_time = datetime.datetime.strptime(departure_time, '%H:%M')
            return (departure_time - arrival_time).seconds // 60
        #ignore every person in the survey, not starting or ending at home (not part of our population) ?
        if (person_df.origin_motive.values[0] != "Home") or (person_df.iloc[-1:].destination_motive.values != "Home"):
            return None
        import re 
        import datetime
        #create a string describing the tours of one person
        #tours = ">".join(list(zip(person_df.origin_motif_time.values, person_df.destination_motif_time.values)))
#        tours = ">".join(person_df.time_motif_time.values)
#        res = re.split(r">\d+:\d+\|Home\|\d+:\d+>", tours)
        tours = ">".join(person_df.time_motif_time.values)
        tours = re.sub(r"(>\d+:\d+\|Home\|\d+:\d+>)", r'\1*', tours)
        res = re.split(r"\*", tours)
        time_dict = {"Work": 0, "School": 0, "University": 0, "Shopping": 0, "Leisure": 0, "Accompany": 0, "Other":0 }
        for tour in res:
            if tour:
                if "Work" in tour:
                    time_dict["Work"] = calc_duration("Work")
                elif "School" in tour:
                    time_dict["School"] = calc_duration("School")
                elif "University" in tour:
                    time_dict["University"] = calc_duration("University")
                elif "Shopping" in tour:
                    time_dict["Shopping"] = calc_duration("Shopping")
                elif "Leisure" in tour:
                    time_dict["Leisure"] = calc_duration("Leisure")
                elif "Accompany" in tour:
                    time_dict["Accompany"] = calc_duration("Accompany")
                elif "Other" in tour:
                    time_dict["Other"] = calc_duration("Other")
                else:
                    continue
        return pd.Series(time_dict)
            
#        regex = r"(\w*)\|(\d\d:\d+)>(\d\d:\d+)"
#        duration_dict = {"Work": 0, "School": 0, "University": 0, "Shopping": 0, "Leisure": 0, "Accompany": 0, "Other":0 }
#        
#        for tup in re.findall(regex, tours):
#            if tup[0] != "Home":
#                arrival = datetime.datetime.strptime(tup[1], '%H:%M')
#                departure = datetime.datetime.strptime(tup[2], '%H:%M')
#                duration_dict[tup[0]] = (departure - arrival).seconds // 60
#        return pd.Series(duration_dict)
    
    def removeOutlier(row):
        l = [x in aoi for x in np.append(row.origin_zone.values, row.destination_zone.values)]
        if all(l):
            return row
        
    
    df = _prepare_emd()
    #df = df.groupby(["sector","sector_fine", "sample_id", "person_id"]).apply(removeOutlier)
    #some entries contain hours 24, 25, 26...
    #transform to values between 0 and 23
    df.depart_hour = pd.to_numeric(df.depart_hour) % 24
    df.depart_hour = df.depart_hour.astype(str)
    df.arrival_hour = pd.to_numeric(df.arrival_hour) % 24
    df.arrival_hour = df.arrival_hour.astype(str)
    df["depart_time"] = df.depart_hour + ":" +df.depart_minute
    df["arrival_time"] = df.arrival_hour + ":" +df.arrival_minute
    df["time_motif_time"] =df.depart_time + "|" + df.destination_motive + "|" + df.arrival_time

    duration_df = df.groupby(["sector","sector_fine", "sample_id", "person_id"]).apply(get_HomeBased_activity_duration)
    duration_df = duration_df.replace(0, np.NaN)
    return duration_df

def activity_start():
    def get_trip_start(person_df, mean=False):
            
        #ignore every person in the survey, not starting or ending at home (not part of our population) ?
        if (person_df.origin_motive.values[0] != "Home") or (person_df.iloc[-1:].destination_motive.values != "Home"):
            return None
        import re 
        import datetime
        #create a string describing the tours of one person
        #tours = ">".join(list(zip(person_df.origin_motif_time.values, person_df.destination_motif_time.values)))
        tours = ">".join(person_df.time_motif_time.values)
        tours = re.sub(r"(>\d+:\d+\|Home\|\d+:\d+>)", r'\1*', tours)
        res = re.split(r"\*", tours)
        #res = re.split(r">\d+:\d+\|Home\|\d+:\d+>", tours)
        
        time_dict = {"Work": 0, "School": 0, "University": 0, "Shopping": 0, "Leisure": 0, "Accompany": 0, "Other":0 }
        for tour in res:
            if tour:
                starting_time = re.findall('\d+:\d+', tour)[0]
                starting_time = (datetime.datetime.strptime(starting_time, '%H:%M') - datetime.datetime.strptime("0:0", '%H:%M')).seconds // 3600
                if "Work" in tour:
                    time_dict["Work"] = starting_time
                elif "School" in tour:
                    time_dict["School"] = starting_time
                elif "University" in tour:
                    time_dict["University"] = starting_time
                elif "Shopping" in tour:
                    time_dict["Shopping"] = starting_time
                elif "Leisure" in tour:
                    time_dict["Leisure"] = starting_time
                elif "Accompany" in tour:
                    time_dict["Accompany"] = starting_time
                elif "Other" in tour:
                    time_dict["Other"] = starting_time
                else:
                    continue
        return pd.Series(time_dict)
    
    def removeOutlier(row):
        l = [x in aoi for x in np.append(row.origin_zone.values, row.destination_zone.values)]
        if all(l):
            return row
        
    
    df = _prepare_emd()
    #df = df.groupby(["sector","sector_fine", "sample_id", "person_id"]).apply(removeOutlier)
    #some entries contain hours 24, 25, 26...
    #transform to values between 0 and 23
    df.depart_hour = pd.to_numeric(df.depart_hour) % 24
    df.depart_hour = df.depart_hour.astype(str)
    df.arrival_hour = pd.to_numeric(df.arrival_hour) % 24
    df.arrival_hour = df.arrival_hour.astype(str)
    df["depart_time"] = df.depart_hour + ":" +df.depart_minute
    df["arrival_time"] = df.arrival_hour + ":" +df.arrival_minute
    df["time_motif_time"] =df.depart_time + "|" + df.destination_motive + "|" + df.arrival_time

    duration_df = df.groupby(["sector","sector_fine", "sample_id", "person_id"]).apply(get_trip_start)
    duration_df = duration_df.replace(0, np.NaN)
    return duration_df


if __name__ == "__main__":
    df = _emd()
    omtl_df = mean_trip_length(mean= True)
    omtl_df.to_csv("travel_time_observed.csv")
    ab_df = get_activity_behaviour()
    
    ad_df = activity_duration()
    dist={}
    for col in ad_df.columns:
        dist[col] = ad_df[col].value_counts()/ad_df[col].value_counts().sum()
        fn = col+"_Duration_probabilities.csv"
        dist[col].to_csv(fn)
    ad_df = pd.DataFrame(dist)
    ad_df = df.fillna(0)
    ad_df.to_csv("Duration_Probabilities.csv")
    
    as_df = activity_start()
    dist = {}
    for col in as_df.columns:
        dist[col] = as_df[col].value_counts()/as_df[col].value_counts().sum()
        fn = col+"_StartingTime_probabilities.csv"
        dist[col].to_csv(fn)
    as_df = pd.DataFrame(dist)
    as_df = df.fillna(0)
    as_df.to_csv("Startingtime_Probabilities.csv")
    