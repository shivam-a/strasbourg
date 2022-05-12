# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 14:20:32 2018

@author: slehmler
"""
import pandas as pd
import configparser
config = configparser.ConfigParser()
config.read("CONFIG.txt")
areatype = config["basic information"]["area type"]
aoi = [c for c in config["basic information"]["areas of interest"].split(',')]
#read the census file
#rename the age-groups of interest
#return dataframe with population (in age_group) per IRIS

def get_population():
    df = pd.read_excel(config["inputfiles"]["census_file"], skiprows = 5)
    rename = {"P14_POP0014":"00_14",	
              "P14_POP1529":"15_29",
              "P14_POP3044":"30_44",
              "P14_POP4559":"45_59",
              "P14_POP6074":"60_74",
              "P14_POP75P":"75_"}
    
    pop_df = df.rename(index=str, columns=rename)[list(rename.values()) + ["IRIS"]]
    pop_df = pop_df[pop_df[areatype].isin(aoi)]
    pop_df = pop_df.set_index("IRIS")
    return pop_df

if __name__ == "__main__":
    df = get_population()
    df.to_csv(config["inputfiles"]["population_file"])