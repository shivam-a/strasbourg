# -*- coding: utf-8 -*-
"""
Created on Fri Aug 10 09:18:17 2018

@author: slehmler
"""
import pandas as pd

##
#Create "Duration_Probabilities.csv" and "Startingtime-Probabilities.csv" 
#from separated csv's containing time resp. duration for each activity  
##

work = "Work_Duration_probabilities.csv"
work_df = pd.read_csv(work, names = ["Work"],index_col = 0 )
school = "School_Duration_probabilities.csv"
school_df = pd.read_csv(school, names = ["School"],index_col = 0 )
university = "University_Duration_probabilities.csv"
university_df = pd.read_csv(university, names = ["University"],index_col = 0 )
leisure = "Leisure_Duration_probabilities.csv"
leisure_df = pd.read_csv(leisure, names = ["Leisure"],index_col = 0 )
shopping = "Shopping_Duration_probabilities.csv"
shopping_df = pd.read_csv(shopping, names = ["Shopping"],index_col = 0 )
accompany = "Accompany_Duration_probabilities.csv"
accompany_df = pd.read_csv(accompany, names = ["Accompany"],index_col = 0 )
other = "Other_Duration_probabilities.csv"
other_df = pd.read_csv(other, names = ["Other"],index_col = 0 )

df = pd.concat([work_df, school_df, university_df, leisure_df, shopping_df, accompany_df, other_df], axis=1)
df = df.fillna(0)
df.to_csv("Duration_Probabilities.csv")

work = "Work_StartingTime_probabilities.csv"
work_df = pd.read_csv(work, names = ["Work"],index_col = 0 )
school = "School_StartingTime_probabilities.csv"
school_df = pd.read_csv(school, names = ["School"],index_col = 0 )
university = "University_StartingTime_probabilities.csv"
university_df = pd.read_csv(university, names = ["University"],index_col = 0 )
leisure = "Leisure_StartingTime_probabilities.csv"
leisure_df = pd.read_csv(leisure, names = ["Leisure"],index_col = 0 )
shopping = "Shopping_StartingTime_probabilities.csv"
shopping_df = pd.read_csv(shopping, names = ["Shopping"],index_col = 0 )
accompany = "Accompany_StartingTime_probabilities.csv"
accompany_df = pd.read_csv(accompany, names = ["Accompany"],index_col = 0 )
other = "Other_StartingTime_probabilities.csv"
other_df = pd.read_csv(other, names = ["Other"],index_col = 0 )

df = pd.concat([work_df, school_df, university_df, leisure_df, shopping_df, accompany_df, other_df], axis=1)
df = df.fillna(0)
df.to_csv("Startingtime_Probabilities.csv")