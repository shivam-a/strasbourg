# -*- coding: utf-8 -*-
"""
Created on Mon May  7 12:20:04 2018

@author: slehmler
"""
from collections import defaultdict
import pandas as pd
import geopandas as gpd 
import overpass
api = overpass.API()
import time
import configparser
config = configparser.ConfigParser()
config.read("CONFIG.txt")



# I want a dataframe that contains:
# Area_ID | Work_Attract | School_Attractor | ....

def get_attraction_vector(aoi, shp_file, tag_file, method="basic"):
    if method == "basic":
        return _basic_method(aoi, shp_file, tag_file)
    elif method == "france":
        return _france_method(aoi, shp_file)
    else:
        raise ValueError('get_attraction_vector : "{}" is not an accepted method.'.format(method))

#method "france" should implement the SIRENE-based method for activity vector estimation that Jordan used     
#TODO:
#basicaly everything, just started implementing it
def _france_method(aoi, shp_file):
    import re
    import numpy as np
    
    ##
    #work
    ##
    print("read files")
	
    sirene_file = config["for av_france"]["sirene"]
    sirene_df = pd.read_csv(sirene_file, encoding="latin-1", dtype={"CODE_IRIS":object})
    print(sirene_df)
    #to get the number of employees from Sirene, we take the middle value of the range given in LIBTEFET
    #TODO:
    #I think that is what Jordan did, but is it really a good approach? a lot of establishments have 0 employees 
    sirene_df["nb_employee"] = sirene_df["LIBTEFET"].apply(lambda row : np.mean(list(map(int, re.findall('\d+', row)))))
    #(I add one to each case with 0 employee)
    sirene_df["nb_employee"] = sirene_df["nb_employee"].fillna(1)
    sirene_df["nb_employee"] = sirene_df["nb_employee"].replace(0, 1)
    
    print("Work")
    work_av = sirene_df.groupby("CODE_IRIS")["nb_employee"].sum()
    work_av = work_av.rename("Work")
    #work_av.index = work_av.index.astype('object')
    
    print("Shopping")
    #shopping
    naf_file = config["for av_france"]["naf_codes"] #naf code defines type of business  
    naf_df = pd.read_excel(naf_file)
    #remove "." from code
    naf_df['Code'] = naf_df['Code'].map(lambda x: str(x).replace(".",""))
    naf_df = naf_df[["Code",'number of visitors per employee \n[nombre de visiteurs par employé]']]
    # APET700: Activité principale de l'entreprise en 712 classes
    naf_df = pd.merge(sirene_df, naf_df, left_on = "APET700", right_on = "Code")
    naf_df["Shopping"] = naf_df["nb_employee"] * naf_df['number of visitors per employee \n[nombre de visiteurs par employé]']
    #shopping_av =  naf_df[["CODE_IRIS","Shopping"]].groupby("CODE_IRIS").sum()
    shopping_av =  naf_df.groupby("CODE_IRIS")["Shopping"].sum()
    #shopping_av.index = shopping_av.index.astype('object')
    
    #load iris shp
    iris_gdf = gpd.read_file(shp_file)
    iris_gdf = iris_gdf[iris_gdf["CODE_IRIS"].isin(aoi)]
    
    #leisure
    leisure_file = config["for av_france"]["leisure"]
    activities = gpd.read_file(leisure_file)
    leisure = activities[activities.CATEGORIE.isin(["Sport", "Culture et loisirs"])]
    leisure["Leisure"] = leisure.area * 19# * bosserhoff

    #school
    school_file = config["for av_france"]["school"]
    school = gpd.read_file(school_file)
    school["School"] = school["Nombre_d_e"]
    
    #university
    uni_file = config["for av_france"]["uni"]
    uni = gpd.read_file(uni_file)
    uni["University"] = uni["Nombre_d_e"]
    

    usl_av = gpd.sjoin(iris_gdf[["CODE_IRIS","geometry"]],uni[["University","geometry"]].append(school[["School","geometry"]]).append(leisure[["Leisure","geometry"]]), how="left")
    usl_av = usl_av.dissolve(by="CODE_IRIS",aggfunc="sum")[["Leisure","School","University"]]

    av_df = pd.concat([work_av, usl_av, shopping_av], axis=1)
    #av_df = usl_av.join(work_av).join(shopping_av)
    av_df = av_df.fillna(0)
    #Accompany as a mixture of other activities, as given by Jordan (without home)
    av_df["Accompany"] = av_df.School*0.55+av_df.Leisure*0.16+av_df.Shopping*0.12+av_df.University*0.10+av_df.Work*0.07 
    av_df["Other"] = 1
    return av_df[av_df.index.isin(aoi)]
    #return work_av.join([school_av, university_av, leisure_av, shopping_av])


    



#implementation of the purely OpenStreetMap based approach
def _basic_method(aoi, shp_file, tag_file):
    #read iris shapefile, transform to WGS84 and get the bounding box of each iris
    gdf = gpd.read_file(shp_file)
    gdf = gdf[gdf["CODE_IRIS"].isin(aoi)]
    gdf = gdf.to_crs(epsg=4326)
    gdf[['minx', 'miny', 'maxx', 'maxy']] = gdf["geometry"].bounds
    
    #read the tag-file, containing the OSM-tags to be searched and their weights
    tag_df = pd.read_csv(tag_file, sep=";") #used by Jordan to get ratio of activities for buildings with OSM tags (Bosserhof)
    
    dic_list = []
    total = str(gdf.shape[0])
    gdf = gdf.reset_index()
    #iterate areas of interest
    #could also be done with an apply function
    for row in gdf.iterrows():
        area = row[1]["CODE_IRIS"]
        min_lat = row[1]['miny']
        min_lon = row[1]['minx']
        max_lat = row[1]['maxy']
        max_lon = row[1]['maxx']
        print(str(row[0])+"/"+total)   
        print(area)
        dic = defaultdict(int)
        dic["area"] =  area
        ##create query for area containing all the tags of interest
        #TODO:
        # actually the tags do not have to be reinserted for each area, just the bounding box 
        q = "("
        for _, tag_row in tag_df.iterrows():
            key = tag_row["tag"]+"="+tag_row["value"]
            q = q+'node[{0}]{1};way[{0}]{1};'.format(key, str((min_lat, min_lon, max_lat, max_lon)))

        q = q+ ');(._;>;);'
        #get the api response
        #as api calls sometime lead to errors, I use a loop and try/except to catch the error and re-try until I get an response
        response = ""
        while response == "":
            try:
                response = api.Get(q)
            except:
                time.sleep(10.0)
        #there is no straightforward way to get the number of entities (f.e. schools) from the returned geojson
        #so i have to do some data-wrangling to get the counts
        gdf_for_count = gpd.GeoDataFrame([x["properties"] for x in response["features"]])
        gdf_for_count = pd.melt(gdf_for_count, value_vars=set.intersection(set(tag_df["tag"]), set(gdf_for_count)), var_name='tag', value_name='value').dropna()
        counts = gdf_for_count.groupby(['tag','value']).size().reset_index().rename(columns={0:'count'})
        
        #not every tag should be counted for each activity, so I multiply with the weights from "overpass_tags.csv" and sum up
        merged = pd.merge(tag_df, counts)
        for activity in list(merged)[2:-1]:
            dic[activity] = sum(merged[activity]*merged["count"])
        dic_list.append(dic)
        #time.sleep(5.0)
    print("finished")
    return pd.DataFrame(dic_list)
    
if __name__ == "__main__":
    aoi = [c for c in config["basic information"]["areas of interest"].split(',')]
    shp_file = config["inputfiles"]["shp_file"]
    tag_file = config["inputfiles"]["tag_file"]
    method = config["attraction vector"]["method"]
    method = "france"
    df = get_attraction_vector(aoi, shp_file, tag_file, method)
    df.to_csv(config["inputfiles"]["av_file"])
    

