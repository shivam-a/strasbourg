# -*- coding: utf-8 -*-
"""
Created on Fri Aug 10 10:18:39 2018

@author: slehmler
"""

import pickle
import pandas as pd
import os
#config file containing inputfile location etc.
import configparser
config = configparser.ConfigParser()
config.read("CONFIG.txt")


with open("input/trips.pkl","rb") as rf:
        trips_dic = pickle.load(rf)
        
ds_file = config.get("inputfiles", "ds_file")
if os.path.isfile(ds_file):
    print("reading distance matrix from precalculated file")
    ds_df = pd.read_csv(ds_file)
    ds_df = ds_df.rename(columns={"Unnamed: 0" : "area"})
    ds_df = ds_df.set_index("area")

#dic = {}
columns = []
nest = []
for activity in trips_dic:
    trips_df = trips_dic[activity].round()
    l = []
    columns.append(activity)
    for row in trips_df.iterrows():
        origin = row[0]
        row_df = row[1]
        for cell in row_df.iteritems():
            destination = cell[0]
            nb = int(cell[1])
            distance = ds_df[destination][origin]
            for i in [distance]*nb:
                l.append(i)
    #dic[activity] = l
    nest.append(l)
import itertools
df = pd.DataFrame((_ for _ in itertools.zip_longest(*nest)), columns=columns)
df.plot.kde(title="Travel Time Distribution")