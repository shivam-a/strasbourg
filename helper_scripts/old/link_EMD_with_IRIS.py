# -*- coding: utf-8 -*-
"""
Created on Thu Aug 23 11:35:45 2018

@author: slehmler
"""

import pandas as pd
import numpy as np
import configparser
config = configparser.ConfigParser()
config.read("CONFIG.txt")

deplacements = pd.read_csv(config["inputfiles"]["survey folder"]+"DEPLACEMENTS.csv",sep=";", dtype=str )
#["D3", "D7"]

iris_zonefine = "X:\\Projects\\OnGoing\\P11GD\\WP04 CityMob\\04_SNCF\\1_data\\shape\\iris_zf_RJ.xls"
matching_df = pd.read_excel(iris_zonefine, sheet_name = 1)

def zf_to_iris(row):
    iris = matching_df[matching_df["Id_zf_cere"] == int(row.D3)].CODE_IRIS.values
    if iris.any():
        d3 = str(iris[0])
    else:
        d3 = ""
    iris = matching_df[matching_df["Id_zf_cere"] == int(row.D7)].CODE_IRIS.values
    if iris.any():
        d7 = str(iris[0])
    else:
        d7 = ""
    return d3,d7
        

deplacements[["D3", "D7"]] = deplacements.apply(zf_to_iris,axis=1, result_type="expand")

aoi = [c for c in config["basic information"]["areas of interest"].split(',')]

people = pd.read_csv(config["inputfiles"]["survey folder"]+"PERSONNES.csv", sep=";", dtype=str)
rename_dic = {"DTIR": "sector",
              "PTIR": "sector",
        "DP2": "sector_fine",
        "PP2":"sector_fine",
        "ECH": "sample_id",
        "PER": "person_id"}
people = people.rename(columns=rename_dic)
deplacements = deplacements.rename(columns=rename_dic)
df = pd.merge(deplacements, people, on = ["sector", "sector_fine", "person_id","sample_id"], how = 'left' )

def printOutlier(row):
    l = [x in aoi for x in np.append(row.D3.values, row.D7.values)]
    if all(l):
        return row
    elif any(l):
        print(l)
    else:
        print("False")
        
d = df.groupby(["sector","sector_fine", "sample_id", "person_id"]).apply(printOutlier)

d.to_csv("emd_prepared.csv")