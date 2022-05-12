
# coding: utf-8

# ### Introduction to Geospatial Data in Python
# https://www.datacamp.com/community/tutorials/geospatial-data-python

# In[10]:

######################
# testing dll and numpy problems
######################
import logging

logging.captureWarnings(False)
import gdal

logging.captureWarnings(False)
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


################################


# Load all importance packages
import geopandas
import numpy as np
import pandas as pd
from shapely.geometry import Point

import missingno as msn
import matplotlib.pyplot as plt

##get_ipython().run_line_magic('matplotlib', 'inline')


# In[11]:


# Getting to know GEOJSON file:
country = geopandas.read_file(r"X:\Groups\N41\GROUP-ORGA\MOBILITY_cluster\Activities\Traffic_model\a_matsim_pop_gen\matsim_pop_gen_Strasbourg\geopandas_bokeh_map\data_test\gz_2010_us_040_00_5m.json")
head = country.head()
print (head)


country.plot()

# Exclude Alaska and Hawaii for now
country[country['NAME'].isin(['Alaska','Hawaii']) == False].plot(figsize=(30,20), color='#3B3C6E');


# In[17]:


# data fromhttp://flhurricane.com/cyclone/stormhistory.php?p=1&year=2018&storm=6
florence = pd.read_csv(r'X:\Groups\N41\GROUP-ORGA\MOBILITY_cluster\Activities\Traffic_model\a_matsim_pop_gen\matsim_pop_gen_Strasbourg\geopandas_bokeh_map\data_test\florence.csv')
florence.head()


# ## Exploratory Data Analysis
# 
# This is always the first thing you do when loading any dataset:
# 
#     Checking the information, data type
#     Any missing value
#     Statistical data
# 

# In[18]:


florence.info()


# Checking missing values using the missingno package. This is a useful package using visualization to show missing data. As you can see below, there's only one missing value in the column "Forecaster" which you don't need for this tutorial. So you can ignore it for now

# In[19]:


# Notice you can always adjust the color of the visualization
msn.bar(florence, color='darkolivegreen');


# Take a look at some statistical information, some could be very useful such as mean wind speed, maximum and minimum wind speed of this hurricane, etc.

# In[20]:


# Statistical information
florence.describe()


# In[21]:


# dropping all unused features:
florence = florence.drop(['AdvisoryNumber', 'Forecaster', 'Received'], axis=1)
florence.head()


# Normally, if you plot the data by itself, there is no need to take extra care for the coordinate. However, if you want it to look similar to how you look on the map, it's important to check on the longitude and latitude. Here the longitude is west, you will need to add "-" in front of the number to correctly plot the data:

# In[22]:


# Add "-" in front of the number to correctly plot the data:
florence['Long'] = 0 - florence['Long']
florence.head()


# Then you can combine Lattitude and Longitude to create hurricane coordinates, which will subsequently be turned into GeoPoint for visualization purpose.

# In[23]:


# Combining Lattitude and Longitude to create hurricane coordinates:
florence['coordinates'] = florence[['Long', 'Lat']].values.tolist()
florence.head()


# In[24]:


# Change the coordinates to a geoPoint
florence['coordinates'] = florence['coordinates'].apply(Point)
florence.head()


# Checking the type of the florence dataframe and column coordinates of florence data. It's pandas DataFrame and pandas Series.

# In[25]:


type(florence)


# In[26]:


type(florence['coordinates'])


# After converting the data into geospatial data, we will check the type of florence dataframe and column coordinates of Florence data again. Now it's Geo DataFrame and GeoSeries.

# In[28]:


# Convert the count df to geodf
florence = geopandas.GeoDataFrame(florence, geometry='coordinates')
florence.head()


# In[29]:


type(florence)


# In[30]:


type(florence['coordinates'])


# Notice that even though it's now a Geo DataFrame and Geo Series, it still behaves like a normal DataFrame and a Series. This means you can still perform filtering, groupby for the dataframe or extract the min, max, or mean values of the column.

# In[31]:


# Filtering from before the hurricane was named.
florence[florence['Name']=='Six']


# In[32]:


# Groupping by name to see how many names it has in the data set:
florence.groupby('Name').Type.count()


# In[33]:


print("Mean wind speed of Hurricane Florence is {} mph and it can go up to {} mph maximum".format(round(florence.Wind.mean(),4),
                                                                                         florence.Wind.max()))


# ### Visualization

# Similar to pandas Dataframe, a GeoDataFrame also has .plot attribute. However, this attribute makes use of the coordinate within the GeoDataFrame to map it out. Let's take a look:

# In[34]:


florence.plot(figsize=(20,10));


# What happened? All you can see is a bunch of points with no navigation. Is there anything wrong?
# No, it's all fine. Because this dataframe only have coordinates information (location) of hurricane Florence at each time point, we can only plot the position on a blank map.
# 
# So, the next step is plotting the hurricane position on the US map to see where it hit and how strong it was at that time. To do so, you will use the US map coordinates (data we loaded in the beginning) as the base and plotting hurricane Florence position on top of it.

# In[35]:


# Plotting to see the hurricane overlay the US map:
fig, ax = plt.subplots(1, figsize=(30,20))
base = country[country['NAME'].isin(['Alaska','Hawaii']) == False].plot(ax=ax, color='#3B3C6E')

# plotting the hurricane position on top with red color to stand out:
florence.plot(ax=base, color='darkred', marker="*", markersize=10);


# Looks great! Now, we will finish it with more details such as:
# 
#     Adding title
#     Color the hurricane position based on the wind speed to see how strong the hurricane was when it hit each city.
#     Remove axis
#     Add legend
#     Saving the result to an image file to use later
# 

# In[36]:


fig, ax = plt.subplots(1, figsize=(20,20))
base = country[country['NAME'].isin(['Alaska','Hawaii']) == False].plot(ax=ax, color='#3B3C6E')
florence.plot(ax=base, column='Wind', marker="<", markersize=10, cmap='cool', label="Wind speed(mph)")
_ = ax.axis('off')
plt.legend()
ax.set_title("Hurricane Florence in US Map", fontsize=25)
plt.savefig('Hurricane_footage.png',bbox_inches='tight');

