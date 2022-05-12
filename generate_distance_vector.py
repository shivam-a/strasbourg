# -*- coding: utf-8 -*-
"""
Created on Fri May 18 13:12:16 2018

@author: slehmler
"""

import pandas as pd
import geopandas as gpd 
from subprocess import Popen, PIPE, STDOUT
import requests
import configparser
config = configparser.ConfigParser()
config.read("CONFIG.txt")


def get_distance_vector(aoi, shp_file,method="euclidean distance"):
    if method == "euclidean distance":
        return _euclidean_distance(aoi, shp_file)
    elif method == "open trip planner":
        return _otp(aoi, shp_file)
    else:
        raise ValueError('get_distance_vector : "{}" is not an accepted method.'.format(method))

def _euclidean_distance(aoi, shp_file, average_travel_time = 500):
    #read iris shapefile, transform to WGS84 and get the bounding box of each iris
    gdf = gpd.read_file(shp_file)
    gdf = gdf[gdf["CODE_IRIS"].isin(aoi)]
    #gdf = gdf.to_crs(epsg=4326)
    gdf["centroid"] = gdf["geometry"].centroid
    lol =  []
    for c1 in gdf.centroid:
        lol.append([c1.distance(c2) for c2 in gdf.centroid])
    #average_travel_time in minutes
    return pd.DataFrame(lol, columns=aoi, index = aoi ) / average_travel_time


def _otp(aoi, shp_file):
    print("starting otp-server")
    p = Popen(['java', '-Xmx2G', '-jar', './otp/otp-1.2.0-shaded.jar','--build', './otp/graphs/strasbourg', '--inMemory', '--port', '8803', '--securePort', '8804'], stdout=PIPE, stderr=STDOUT)
    for line in p.stdout:
        print(line)
        if b"Grizzly server running" in line:
            break
    print("continuing######################")
    gdf = gpd.read_file(shp_file)
    gdf = gdf[gdf["CODE_IRIS"].isin(aoi)]
    gdf = gdf.to_crs(epsg=4326)
    gdf["centroid"] = gdf["geometry"].centroid
    centroids = list(gdf.centroid)
    lol =  []
    for i, c1 in enumerate(centroids):
        print("getting distances for area {} of {}".format(i, len(centroids)-1))
        l = []
        for y in range(i):
            l.append(lol[y][i])
        l.append(60)
        for c2 in centroids[i+1:]:
            #l.append(c1.distance(c2))
            #get duration of car_trip
            r = requests.get("http://localhost:8803/otp/routers/default/plan?fromPlace={},{}&toPlace={},{}&mode=CAR".format(c1.y, c1.x, c2.y, c2.x)).json()
            duration_car = 10000000

            if 'plan' in r:
                for itinerary in r['plan']['itineraries']:
                    d = itinerary['duration']
                    duration_car = d if d < duration_car else duration_car
            #get duration of bicycle/transit-trip
            r2 = requests.get("http://localhost:8803/otp/routers/default/plan?fromPlace={},{}&toPlace={},{}&mode=BICYCLE,TRANSIT".format(c1.y, c1.x, c2.y, c2.x)).json()
            duration_bt = 10000000
            if 'plan' in r2:
                for itinerary in r2['plan']['itineraries']:
                    d = itinerary['duration']
                    duration_bt = d if d < duration_bt else duration_bt
            print(l)
            print("http://localhost:8803/otp/routers/default/plan?fromPlace={},{}&toPlace={},{}&mode=CAR".format(c1.y, c1.x, c2.y, c2.x))
            l.append(duration_car if duration_car < duration_bt else duration_bt)
        lol.append(l)
    return pd.DataFrame(lol, columns=aoi, index = aoi )/60
    
if __name__ == "__main__":
    aoi = [c for c in config["basic information"]["areas of interest"].split(',')]
    shp_file = config["inputfiles"]["shp_file"]
    method = config["distance matrix"]["method"]
    method = "open trip planner"
    df = get_distance_vector(aoi, shp_file, method)
    #df.to_csv(config["inputfiles"]["ds_file"])
    
    

