# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 16:25:02 2019

@author: slehmler
"""

# using geosine from:
#http://data.cquest.org/geo_sirene/
#explained in:
#https://medium.com/@cq94/g%C3%A9ocodage-de-la-base-sirene-2f0e14e87a8d

import geopandas as gpd
import pandas as pd
import os.path as path
import os

xmin, ymin, xmax, ymax = [7.4923,48.4543, 8.0320, 48.6837]


# reduce geo-sirene to the following variables:
# APET700,TEFET,LIBTEFET,latitude,longitude
sirene = pd.read_csv(path.abspath(path.join(os.getcwd(),"../input/sirene/etablissements_actifs.csv")), encoding="latin-1", sep=",")

with open(path.abspath(path.join(os.getcwd(),"../input/sirene/etablissements_actifs.csv")), 'r', encoding="latin-1") as readfile , open(path.abspath(path.join(os.getcwd(),"../input/sirene/etablissements_actifs_reduced.csv")), 'w', encoding="latin-1") as writefile:
     for line in readfile:
         ll = line.split(",")
         #writefile.write("{},{},{},{},{}\n".format(ll[43],ll[45], ll[46], ll[100], ll[101]))
         #print(ll)
         writefile.write("{},{},{}\n".format(ll[0], ll[100], ll[101]))

#sirene = pd.read_csv(path.abspath(path.join(os.getcwd(),"../input/sirene/etablissements_actifs_reduced.csv")), encoding="latin-1", sep=",", nrows=33447)

sirene_reduced = sirene[["latitude", "longitude", "siren","nic","tefet","libtefet","apen700" ]]
sirene_reduced.to_csv("geo_sirene_reduced.csv",index=False,encoding="latin-1")


#original siren
sirene_full = pd.read_csv(path.abspath(path.join(os.getcwd(),"../input/sirene/sirc-17804_9075_61173_201805_L_M_20180601_020957358.csv")), encoding="latin-1", sep=";")
sirene_geo = pd.read_csv("geo_sirene_reduced.csv",encoding="latin-1")

sirene_full = pd.merge(sirene_full, sirene_geo, left_on=['SIREN','NIC'], right_on=['siren','nic'])
sirene_full = sirene_full[["latitude", "longitude", "siren","nic","tefet","libtefet","apen700" ,"APET700","TEFET","LIBTEFET"]]
gdf = gpd.GeoDataFrame(sirene_full, geometry=gpd.points_from_xy(sirene_full.longitude, sirene_full.latitude))
gdf = gdf.cx[xmin:xmax, ymin:ymax]

iris = gpd.read_file(path.abspath(path.join(os.getcwd(),"../input/shapefile/CONTOURS-IRIS/CONTOURS-IRIS.shp")))
iris = iris.to_crs(epsg=4326)
sirene_iris = gpd.sjoin(gdf, iris)
sirene_iris[["CODE_IRIS",'APET700', 'TEFET', 'LIBTEFET']].to_csv("sirene_with_iris.csv", index=False, encoding="latin-1")
