# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 11:22:42 2018

@author: slehmler
"""
import pandas as pd

observed_Duration = "X:\\Projects\\OnGoing\\P11GD\\WP02\\2018\\Transportation modeling\\Tour based modeling\\population generation\\automatize population - Nantes\\input\\Time\\Duration_Probabilities.csv"
df = pd.read_csv(observed_Duration, index_col = 0)
df.plot.area(title="Observed Activity Duration (in minutes)", subplots=True)

observed_StartingTime = "X:\\Projects\\OnGoing\\P11GD\\WP02\\2018\\Transportation modeling\\Tour based modeling\\population generation\\automatize population - Nantes\\input\\Time\\StartingTime_Probabilities.csv"
df = pd.read_csv(observed_StartingTime, index_col = 0)
df.plot.area(title="Observed Activity Starting Time (in hours)", subplots=True)