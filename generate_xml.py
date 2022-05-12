# -*- coding: utf-8 -*-
"""
Created on Fri Aug 10 09:10:42 2018

@author: slehmler
"""

######################
# testing dll problems
######################

import sys
for path in sys.path:
	print (path)

import gdal
gdal.UseExceptions()

import os
import sys

env_p = sys.prefix  # path to the env
print("Env. path: {}".format(env_p))

new_p = ''
for extra_p in (r"Library\mingw-w64\bin",
    r"Library\usr\bin",
    r"Library\bin",
    r"Scripts",
    r"bin"):
    new_p +=  os.path.join(env_p, extra_p) + ';'

os.environ["PATH"] = new_p + os.environ["PATH"]  # set it for Python
os.putenv("PATH", os.environ["PATH"])  # push it at the OS level
# end#############

import pandas as pd
import geopandas as gpd
import random
from shapely.geometry import  Point
from collections import defaultdict
import numpy as np

import configparser


#####################
# Input
#####################
config = configparser.ConfigParser()
config.read("CONFIG.txt")



def population_to_xml(trips_dic, ds_df, aoi, ten_percent =True):
    shp_file = config["inputfiles"]["shp_file"]
    #read shapefile

    france = gpd.read_file(shp_file)
    #change coordinate projection from lambert93(Insee) to wgs84(OpenStreetMap)
    #france = france.to_crs(epsg=4326)
    poly_dic = {iris:france.loc[france['CODE_IRIS'] == iris]['geometry'].iloc[0] for iris in aoi}
    boundaries_dic = {iris:france.loc[france['CODE_IRIS'] == iris]['geometry'].iloc[0].bounds for iris in aoi}

    startTime_distribution = pd.read_csv(config["inputfiles"]["starting times"])
    duration_distribution = pd.read_csv(config["inputfiles"]["durations"])
    for_vis = defaultdict(list)
    if ten_percent: 
        filename = "population_10p.xml"
    else:
        filename = "population.xml"
    with open(filename, "w") as outfile:
        outfile.write("""<?xml version="1.0" ?>
                      <!DOCTYPE plans SYSTEM "http://www.matsim.org/files/dtd/plans_v4.dtd">
                      <plans>
                      """)
        current_id = 0 
        for activity in trips_dic:
            print(activity)
            trip_matrix = trips_dic[activity]
            #print(trip_matrix)
            for row in trip_matrix.iterrows():
                origin = row[0]
                OriginIris_bounds = boundaries_dic[str(origin)]
                OriginIris_poly = poly_dic[str(origin)]
                trip_series = row[1].apply(lambda x: int(round(x))) #as the trips contian many  non-zero but below one values, I round up (0.0005 -> 1)
                for cell in trip_series.iteritems():
                    destination = cell[0]
                    DestinationIris_bounds = boundaries_dic[str(destination)]
                    DestinationIris_poly = poly_dic[str(destination)]
                    number_of_trips = cell[1]
                    for i in range(number_of_trips):
                        #for 10% sample
                        if ten_percent:
                            drop = np.random.choice([0, 1], p=[0.1,0.9])
                            if drop:
                                continue
                        #time?random (for now)
                        #h = np.random.choice(range(5,13), p=[0.1,0.15,0.2,0.3,0.1,0.05,0.05,0.05])
                        h = np.random.choice(startTime_distribution[activity].index, p=startTime_distribution[activity])
                        m,s = np.random.randint(0,60,2)
                        startTime = "%02d:%02d:%02d" % (h, m, s)
                        #h = np.random.choice(range(14,22), p=[0.05,0.05,0.15,0.2,0.3,0.15,0.05,0.05])
                        duration = np.random.choice(duration_distribution[activity].index, p=duration_distribution[activity])
                        h = h + 0.5 + duration/60
                        m,s = np.random.randint(0,60,2)
                        endTime = "%02d:%02d:%02d" % (h, m, s)
                        #location?random based on iris-shapefile?
                        #Startlocation
                        while True:
                            StartLocation = Point(random.uniform(OriginIris_bounds[0],OriginIris_bounds[2]),
                                                  random.uniform(OriginIris_bounds[1], OriginIris_bounds[3]))
                            if OriginIris_poly.contains(StartLocation):
                                break
                        #EndLocation
                        while True:
                            EndLocation = Point(random.uniform(DestinationIris_bounds[0],DestinationIris_bounds[2]),
                                                  random.uniform(DestinationIris_bounds[1], DestinationIris_bounds[3]))
                            if DestinationIris_poly.contains(EndLocation):
                                break
                        #add id, type, mode, location and time to the template below:
                        new_person = """
    <person id= "{0}">
        <plan>
            <act type= "home" x="{1}" y="{2}" end_time= "{3}" />
            <leg mode= "car" />
            <act type= "{7}" x="{4}" y="{5}" end_time= "{6}" />
            <leg mode= "car" />
            <act type= "home" x="{1} " y="{2}" />
        </plan>
    </person>
                    """.format(current_id,
                        StartLocation.x,StartLocation.y,startTime,
                        EndLocation.x,EndLocation.y,endTime,
                        activity)
                        outfile.write(new_person)
                        
                        for_vis[activity].append(ds_df.at[origin,str(destination)])
                        current_id += 1
        outfile.write("</plans>")