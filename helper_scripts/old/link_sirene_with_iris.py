# -*- coding: utf-8 -*-
"""
Created on Thu Jun 14 14:52:19 2018

@author: slehmler
"""
import requests 
from shapely.geometry import Point
import pandas as pd
import geopandas as gpd

import configparser
config = configparser.ConfigParser()
config.read("CONFIG.txt")

sirene_file = "input/sirene/sirc-17804_9075_61173_201805_L_M_20180601_020957358.csv"
siren_codeiris = "sirene_codeIris.csv"
sirene_with_iris = pd.read_csv(siren_codeiris)
sirene = pd.read_csv(sirene_file, sep = ";", encoding="latin-1")
df = pd.merge(sirene_with_iris, sirene, on=["SIREN","NIC"])

#"https://nominatim.openstreetmap.org/search.php?q=steinstra%C3%9Fe+27a%2C+karlsruhe&format=json"
#base_url = "https://nominatim.openstreetmap.org/search.php?q={}&format=json"
#base_url = "http://maps.googleapis.com/maps/api/geocode/json?address={}"

#aoi= [c for c in config["basic information"]["areas of interest"].split(',')]
#print("reading sirene")
#sirene_file = "C:\\FILES\\downloads\\geo_sirene.csv\\geo_sirene.csv"
#sirene_df = pd.read_csv(sirene_file)
##print("preparing sirene")
#sirene_df = sirene_df[["SIREN","NIC","longitude","latitude"]]
#sirene_df.to_csv("extract.csv")
#sirene_df = pd.read_csv("extract.csv")
#crs = {'init': 'epsg:4326'}
#def geom(row):
#    return Point(float(row["longitude"]),float(row["latitude"]))
#sirene_df["geometry"] = sirene_df.apply(geom,axis=1)
#sirene_df = sirene_df.dropna()
#sirene_gdf = gpd.GeoDataFrame(sirene_df, crs=crs, geometry=sirene_df["geometry"])
#print("reading iris shp")
###read shapefile of iris
#iris = gpd.read_file(config["inputfiles"]["shp_file"])
#iris = iris.to_crs(epsg=4326)
#iris = iris[iris["CODE_IRIS"].isin(aoi)]
#sirene_gdf.crs = iris.crs
#
#print("spatial join")
###spatial join of sirene and iris
#sirene_with_iris = gpd.sjoin(sirene_gdf, iris, how="inner", op='intersects')
#sirene_with_iris[["SIREN", "NIC", "CODE_IRIS"]].to_csv("sirene_codeIris.csv", index=False)
#use data from: http://data.cquest.org/geo_sirene/
#https://medium.com/@cq94/g%C3%A9ocodage-de-la-base-sirene-2f0e14e87a8d



##we need postal codes of interest 
#inseeCode_to_postalCode = pd.read_csv("input/sirene/insee-postal.csv", sep = ";")
#inseeCode_to_postalCode = inseeCode_to_postalCode[inseeCode_to_postalCode["Code INSEE"].isin(aoi_insee)]
##
###some rows might contain multiple postal codes, separated by "/" : Inseecode | PostalCode1/PostalCode2
#postalCodes = [code for sublist in  [row.split("/") for row in inseeCode_to_postalCode["Code Postal"].values] for code in sublist]
#
##sirene_file = "input/sirene/sirc-17804_9075_61173_201805_L_M_20180601_020957358.csv"
#sirene_file = "X:\\Projects\\OnGoing\\P11GD\\WP02\\2018\\Transportation modeling\\data\\geo_sirene.csv\\geo_sirene.csv"
#l_row = []
#columns = ['L4_NORMALISEE', 'L6_NORMALISEE', 'APET700', 'TEFET', 'LIBTEFET', 'longitude', 'latitude', 'geometry']
#print("reading sirene")
#i = 0
#for row in open(sirene_file, "r",encoding="utf-8"):
#    print(len(l_row))
#    print("of"+ str(i))
#    i += 1
#    #row = row.replace("\"", "").split(";")
#    row = row.replace("'", "").split(",")
##    if not columns:
##        columns = [row[5],row[7],row[42],row[45],row[46],row[-9],row[-8], "geometry"]
#    if row[-8]:
#        if row[7].split(" ")[0] in postalCodes:
#            l_row.append([row[5],row[7],row[42],row[45],row[46],row[-9],row[-8], Point(float(row[-9]),float(row[-8]))])
#sirene_df = pd.DataFrame(l_row, columns = columns)
#
#sirene_df = sirene_df[pd.notnull(sirene_df['L4_NORMALISEE'])]
#sirene_df = sirene_df[sirene_df["L6_NORMALISEE"].apply(lambda row: str(row).split(" ")[0] in postalCodes)]
##remove all the rows that have 'nan' in their adresse field
#
#sirene_df = sirene_df[pd.notnull(sirene_df['L6_NORMALISEE'])]
#
##looking up all businesses in Siren takes too long and needs more API querries than allowed
##that is why we filter for aoi
##get area of interest -> only take the first five digits as these are the insee-code
#
##finally: keep only the businesses that are in the area of interest
##
##import time
###function to be applied to every row
###querries osm/nominatim-api and returns the lon/lat-Point 
##def get_location(row):
##    #get adresse and postcode,City
##    #time.sleep(1)
##    print(row)
##    q = base_url.format(row["L4_NORMALISEE"] + ", "+" ".join(row["L6_NORMALISEE"].split(" ")[:2]))
##    try:
##        r = requests.get(q)
##        print(r)
##        r = r.json()
##        if r:
##            return Point( float(r[0]['lon']), float(r[0]['lat']))
##    except:
##        return 0
##
##
##sirene_df_last = pd.read_csv("input/sirene/sirene_reduced.csv")
###add lon/lat to sirene
##sirene_df = sirene_df_last[sirene_df_last["geometry"] == 0]
##sirene_df["geometry"] = sirene_df.apply(get_location, axis=1)
###some establishments cannot be found with the api, delete those and save results
###sirene_df = sirene_df[pd.notnull(sirene_df["geometry"])]
###sirene_df.to_csv("sirene_withLatLon.csv")
##
##pd.concat([sirene_df_last[sirene_df_last["geometry"] != 0], sirene_df]).to_csv("sirene_reduced.csv",encoding='utf-8-sig',index=False)
##
##change df to geo-dataframe
#print("transforming to geo dataframe")
#crs = {'init': 'epsg:4326'}
#sirene_gdf = gpd.GeoDataFrame(sirene_df, crs=crs, geometry=sirene_df["geometry"])
#
#print("reading iris shp")
##read shapefile of iris
#iris = gpd.read_file(config["inputfiles"]["shp_file"])
#iris = iris.to_crs(epsg=4326)
#sirene_gdf.crs = iris.crs
#print("spatial join")
##spatial join of sirene and iris
#sirene_with_iris = gpd.sjoin(sirene_gdf, iris, how="inner", op='intersects')
#sirene_with_iris[["CODE_IRIS", "APEN700", "TEFET", "LIBTEFET"]].to_csv("sirene_with_iris_full.csv",encoding='utf-8-sig',index=False)
#
