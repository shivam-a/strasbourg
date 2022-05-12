'''
author: sliz
data: 20201207

1. Preporcessing:
-	Geolocalised SIREN addresses and join it with IRIS code
-   Export shp table to txt
-	Open txt using xlxs- in Advanced -maintain the text columns of IRIS_CODE and other if needed
-	Change column name appropriately (column names are cut to 9 characters while exporting from mdb)
2. This script is
-	for join employees code to the table (check column names)
-   for customers estimatin based on NAF code

'''
#!/usr/bin/python
# -*- coding: utf-8 -*

import pandas as pd
import numpy as np
import math
import re
import configparser
config = configparser.ConfigParser()

config.read(r'CONFIG.txt')
############################
# Input
############################
sirene_file = config["for av_france"]["sirene"]
code_employees = config["for av_france"]["code_employees"]
naf_file = config["for av_france"]["naf_codes"]  # naf code defines type of business
############################
#Output
###########################
sirene_with_empl =config["for av_france"]["sirene_with_empl"]
sirene_with_cust =config["for av_france"]["sirene_wrkoing_shopping"]


def calc_employee_siren(sirene_file, code_employees, sirene_with_empl):
    #Read csv
    code_empl_df = pd.read_csv(code_employees, delimiter=';', encoding="ISO-8859-1")
    print(code_empl_df)

    sirene_df = pd.read_csv(sirene_file, delimiter=';',  encoding = "ISO-8859-1",
                            dtype={"CODE_IRIS":str, "siren":int})
    print(sirene_df.columns)
    # Drop some columns
    sirene_df.drop(['Join_Count', 'TARGET_FID'], axis=1, inplace=True)
    #print(sirene_df.columns)
    # Replace 'NaN' to 0 without having to reassign df (nplace =True)
    sirene_df['trancheEffectifsEtablissement'].fillna(0, inplace=True)
    # Replace 'NN' to 0
    sirene_df['trancheEffectifsEtablissement'] = sirene_df['trancheEffectifsEtablissement'].replace('NN', 0)
    #Convert column to int
    sirene_df['trancheEffectifsEtablissement']= sirene_df['trancheEffectifsEtablissement'].astype(int)
    #print(sirene_df.head(20))
    #print(sirene_df.columns)

    #Merge tables
    merge_df = pd.merge(sirene_df, code_empl_df, how='left', left_on='trancheEffectifsEtablissement', right_on='code_tranche')
    print(merge_df.head(6))
    #print(merge_df['code_employees'])

    # to get the number of employees from Sirene, we take the middle value of the range, the balue is round up (math.ceil)
    merge_df["nb_employee"] = merge_df["code_employees"].apply(lambda row : math.ceil(np.mean(list(map(int, re.findall('\d+', str(row)))))))
    # Take the minimum
    merge_df["min_nb_employee"] = merge_df["code_employees"].apply(
        lambda row: math.ceil(np.min(list(map(int, re.findall('\d+', str(row)))))))
    print(sirene_df.head())
    #Save to scv
    merge_df.to_csv(sirene_with_empl, index=False)
    return merge_df

def calc_shopping_siren(sirene_df, naf_file, sirene_with_cust):

    print(sirene_df.columns)
    sirene_df['activitePrincipaleEtablissement'] = sirene_df['activitePr']
    sirene_df['activitePrincipaleEtablissement'] = sirene_df['activitePrincipaleEtablissement'].map(
        lambda x: str(x).replace(".", ""))
    naf_df = pd.read_excel(naf_file)
    # remove "." from code
    naf_df['Code'] = naf_df['Code'].map(lambda x: str(x).replace(".", ""))
    naf_df['nb_customer_per_employee'] = naf_df['number of visitors per employee \n[nombre de visiteurs par employé]']
    naf_df = naf_df[["Code", 'nb_customer_per_employee']]
    # Merge tables
    naf_df = pd.merge(sirene_df, naf_df, left_on = "activitePrincipaleEtablissement", right_on = "Code")
    print(naf_df.head())

    naf_df["Shopping"] = naf_df["nb_employee"] * naf_df ['nb_customer_per_employee']
    naf_df.to_csv(sirene_with_cust, index=False)
    shopping_av = naf_df.groupby("CODE_IRIS")["Shopping"].sum()
    return shopping_av


if __name__ == '__main__':

    df = calc_employee_siren(sirene_file, code_employees, sirene_with_empl )
    calc_shopping_siren(df, naf_file, sirene_with_cust )