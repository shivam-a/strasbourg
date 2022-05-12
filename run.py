# -*- coding: utf-8 -*-
"""
Created on Mon May  7 09:56:39 2018

@author: slehmler
"""
import os
import pandas as pd
import numpy as np

#from numpy.random import choice

#import own scripts
from generate_attraction_vector import get_attraction_vector
#from generate_distance_vector import get_distance_vector
#from generate_activityBehaviour import get_activity_behaviour
#from generate_population import get_population

#config file containing inputfile location etc.
import configparser
config = configparser.ConfigParser()
config.read("CONFIG.txt")

#filter for aoi (areas(IRIS) of interest)
areatype = config["basic information"]["area type"]
aoi = [c for c in config["basic information"]["areas of interest"].split(',')]
print('aoi\n ', aoi)
#read or generate activity_behaviour (= distribution of tour types on age_group)
ab_file = config["inputfiles"]["activityBehaviour_file"]
#if ab-file exist, just read it contents,
if os.path.isfile(ab_file):
    print("reading activity behaviour from precalculated file")
    ab_df = pd.read_csv(ab_file)
    ab_df = ab_df.set_index("age_group")
    print('ab_df', ab_df)
else:
    #otherwise run code contained in "generate_activityBehaviour.py"
    print("No activiy behaviour file found. \n Calculating activity behaviour from survey and save to file")
    ab_df = get_activity_behaviour()
    ab_df.to_csv(ab_file)

#read or generate population (= number of peoples in age_group per IRIS)
pop_file = config["inputfiles"]["population_file"]
#if pop-file exist, just read it contents,
if os.path.isfile(pop_file):
    print("reading population from precalculated file")
    pop_df = pd.read_csv(pop_file)  
    pop_df = pop_df.set_index(areatype)
    print('pop_df', pop_df)
else:
    #otherwise run code contained in "generate_population.py"
    print("No population file found. \n Calculating population from census save to file")
    pop_df = get_population()
    #filter for IRISes of interest
    
    pop_df.to_csv(pop_file)

#multiply the population matrix (IRIS X Age_group) with the activity matrix (age-group X activity)
#create Production Matrix
#IRIS X Activity
#print(np.inner(pop_df, ab_df).shape)
production_df = pop_df.dot(ab_df)
print('production_df:')
print(production_df)

#generate attraction vectors
#using JT's OSM-Approach

av_file = config.get("inputfiles", "av_file")
if os.path.isfile(av_file):
    print("reading attraction vector from precalculated file")
    av_df = pd.read_csv(av_file)
    av_df = av_df.set_index('Unnamed: 0')
else:
    shp_file = config["inputfiles"]["shp_file"]
    tag_file = config["inputfiles"]["tag_file"]
    method = config["attraction vector"]["method"]
    print("No attraction vector file found. \n Calculating attraction using method {} and save to file".format(method))
    av_df = get_attraction_vector(aoi, shp_file, tag_file, method)
    #av_df = av_df.set_index('Unnamed: 0')
    av_df.to_csv(av_file)

#reindex production_df
production_df = production_df.reindex(av_df.index)
print('reindex prod df', production_df)

#TO-DO: 
#generate distance matrix with otp
ds_file = config.get("inputfiles", "ds_file")
if os.path.isfile(ds_file):
    print("reading distance matrix from precalculated file")
    ds_df = pd.read_csv(ds_file)
    ds_df = ds_df.rename(columns={"Unnamed: 0" : "area"})
    ds_df = ds_df.set_index("area")
else:
    shp_file = config["inputfiles"]["shp_file"]
    method = config["distance matrix"]["method"]
    print("No distance matrix file found. \n Calculating distance using method {} and save to file".format(method))
    ds_df = get_distance_vector(aoi, shp_file, method)
    ds_df.to_csv(ds_file)


#round productions and attractions
#scale attractions to productions
#production_df = production_df.round()
#av_df = av_df.round()
#av_df = av_df*(production_df.sum()/av_df.sum())
#av_df = av_df.round()
 
from generate_activityBehaviour import  mean_trip_length

import pickle
omtl_pickle = config.get("dictionaries", "omtl")
if os.path.isfile(omtl_pickle ):
    print("Reading observed mean trip length from file.")
    with open(omtl_pickle ,"rb") as rf:
        omtl = pickle.load(rf)
else:
    print("No observed mean trip length file found. \n Calculating mean trip length and save to file")
    with open(omtl_pickle ,"wb") as wf:
        omtl =  mean_trip_length()
        pickle.dump(omtl,wf)

from gravity_model import get_trip_matrices, calibrate_beta
betas_pickle = config.get("dictionaries", "betas")
if os.path.isfile(betas_pickle):
    print("Reading precalculated betas from file")
    with open(betas_pickle,"rb") as rf:
        betas = pickle.load(rf)
else:
    betas = calibrate_beta(production_df, av_df, ds_df, omtl)
    if betas:
        print("No betas file found. \n Calibrating gravity model and save betas to file")
        with open(betas_pickle,"wb") as wf:
            pickle.dump(betas,wf)
#betas = {"Work": 0.1, "School": 0.1, "University": 0.1, "Shopping": 0.1, "Leisure": 0.1, "Accompany": 0.1, "Other":0.1 }#betas["Work"] = 0.03067269

trips_dic = get_trip_matrices(production_df, av_df, ds_df, betas)
trips_pickle = config.get("dictionaries", "trips")
with open(trips_pickle,"wb") as wf:
	pickle.dump(trips_dic,wf)
	
from generate_xml import population_to_xml

population_to_xml(trips_dic, ds_df, aoi)

