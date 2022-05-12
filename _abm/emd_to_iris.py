'''
author: @sliz
data: 20201119
Usefull links
https://deanla.com/pandas_named_agg.html

Approach for assigning IRIS zones to surves participants
1. In the preporcessing step, EMD zones were oerlapped with IRIS zones and the share of IRIS in EMD was calulated using Tabulate Intersection (ArcMAP)
2. Select individuals with housholds with Home and Home_gatwey activities
'''

import configparser
import os
import sys
import pandas as pd
import math
import random
from pandas import DataFrame

config = configparser.ConfigParser()
# change the root directory to where CONFIG is kept
os.chdir(os.path.dirname(sys.path[0]))
config.read(r'CONFIG.txt')

class Zone_to_Iris_Mapper:
    '''
    Prepare empty dictionary framework
    Distribute people on IRIS
    '''
    def __init__(self):
        self.zone_mapping = {}
        self.distributed_people = {}

    def add_mapping(self, zone, iris_id, people_iris):
        if zone not in self.zone_mapping.keys():
            self.zone_mapping[zone] = []
        self.zone_mapping[zone].append((iris_id, people_iris))

    def get_mapping(self):
        return self.zone_mapping.copy()

    def prepare_distribution(self):
        '''Prepare empty layout for dictionary.
        Sort iris in EMD zones by people count and set count of distributed persons to 0.'''
        for zone_id in self.zone_mapping.keys():
            self.zone_mapping[zone_id] = sorted(self.zone_mapping[zone_id], key=lambda x:x[1])
            for tuple in self.zone_mapping[zone_id]:
                self.distributed_people[(zone_id, tuple[0])] = 0
        self.last_zone_id = 0

    def map_house_zone_to_iris(self, zone_id, home_other_zone_id, person_count):
        '''
        Assign home from EMD to IRIS zone
        '''
        iris_id = -1
        if math.isnan(float(zone_id)):
            # the both cases should not be present in the database,  as the activity chains without home were removed in the preprocessing step
            if math.isnan(float(home_other_zone_id)):
                # in case  home and home_gateway are nan (no home available in the activity chain)
                zone_id = self.last_zone_id
                print('home and home_gateway are nan (no home available in the activity chain)', zone_id)
            else:
                # If the activity chain does not start with Home than Home_getaway is taken as zone_orgin
                zone_id = home_other_zone_id
                print('activity chain does not start with Home than Home_getaway is taken as zone_orgin', zone_id)
        # put home EMD to iris if possible (enough people left to distribute)
        for iris_tuple in self.zone_mapping[zone_id]:
            if iris_tuple[1] <= 0:
                continue
            dist_key = (zone_id, iris_tuple[0])
            # check if we can distribute
            already_distributed = self.distributed_people[dist_key]
            free_people_in_iris_zone = iris_tuple[1] - already_distributed
            if free_people_in_iris_zone < person_count:
                continue
            iris_id = iris_tuple[0]
            self.distributed_people[dist_key] = already_distributed + person_count
            break

        if iris_id == -1:
            # very unlikely but if cannot distribute take into biggest percentage of iris in EMD
            iris_id = self.zone_mapping[zone_id][len(self.zone_mapping[zone_id]) - 1][0]
            self.distributed_people[(zone_id, iris_id)] += person_count
        # piggy trick (shouldn't be here)
        self.last_zone_id = zone_id
        return iris_id

class House_to_iris_map:

    def __init__(self):
        __dict = {}

    def init_from_df(self, loa_grouped_by_houses: DataFrame):
        self.__dict = loa_grouped_by_houses[['sector', 'sector_fine', 'sample_id','Home', 'iris_id']].set_index(
            ['sector', 'sector_fine', 'sample_id']).to_dict('index')

    def get_iris_id(self, sector, sector_fine, sample_id):
        return self.__dict[(sector, sector_fine, sample_id)]['iris_id']

    def get_zone_id(self, sector, sector_fine, sample_id):
        return self.__dict[(sector, sector_fine, sample_id)]['Home']

class Zone_Chain_Mapper:
    '''
    Distribute participants of other activites to IRIS zones
    '''
    def __init__(self, house_to_iris_map: House_to_iris_map, zone_to_iris : DataFrame):
        self.__house_to_iris_map = house_to_iris_map
        self.__zone_to_iris = {}
        zone_to_iris.apply(lambda row: self.__add_zone_to_iris_entry(row['code_emd'], row['CODE_IRIS'], row['PERCENTAGE']), axis=1)

    def __add_zone_to_iris_entry(self, zone_id, iris_id, percentage):
        if zone_id not in self.__zone_to_iris.keys():
            self.__zone_to_iris[zone_id] = []
        self.__zone_to_iris[zone_id].append((iris_id, percentage))

    def map_chain_to_iris_chain(self, sector, sector_fine, sample_id, zone_chain):
        '''
        Replace EMD zone_chain (001004>026015>001004) with IRIS chain (671300101>674822204>671300101) for all activities
        '''
        home_zone = self.__house_to_iris_map.get_zone_id(sector, sector_fine, sample_id) # home: '001004'
        home_iris = self.__house_to_iris_map.get_iris_id(sector, sector_fine, sample_id) # home_iris: '671300101'
        zones = zone_chain.split('>') #zone:['001004', '026015', '001004']
        iris_zones = []
        for zone in zones:
            if zone == home_zone: #'001004'
                # this is home EMD -> replace with home iris
                iris_zones.append(str(home_iris))
            else:
                # other activies than EMD home
                # assign randomly one iris. Take random percentage of iris coverage as weights
                #eg.
                # 1. zone 1 -- iris 1 60%
                #              iris 2 40%
                # 2.generate random 0-100 eg. 50
                # 3.substract coverage of first iris form 100 100-60 =40
                # 4 is substract product < random ? yes -> take iris
                random_perc = random.uniform(0, 100) #random_perc: 55.2
                # Go from 100 to 0 to handle the cases where iris percentage > 100.0 (buggy  Tabulate process of ArcMap )
                current_perc = 100.0
                if zone in self.__zone_to_iris.keys(): #clook for EMD zone in iris zones, if not found then look for the percentage coverage
                    zone_found = False
                    for iris_zone in self.__zone_to_iris[zone]: # iris_zone, percentage: ('671300101', 79.977)
                        # substract percentage coverage of iris
                        current_perc -= iris_zone[1] # -59.97 - 79.97
                        if(current_perc < random_perc):
                            # if percentage left smaller than random add iris id and break
                            iris_zones.append(str(iris_zone[0]))
                            zone_found = True
                            break
                        #else continue and go to next iris
                    if not zone_found:
                        # In case, the sum of percentages of all iris areas in EMD zone was < 100 and random was < (100- percentage sum)
                        iris_zones.append(str(max(self.__zone_to_iris[zone], key= lambda iris_zone: iris_zone[1])[0]))
                else:
                    iris_zones.append('OUT')
        return '>'.join(iris_zones)

# 1 step
def zone_to_iris():
    """
    this function reads the area|percentage file created by any GIS app that shows overlapping area and its percentage
    overlap between survey zone feature and contour iris feature. This helps in generating a zone to iris conversion
    sheet
    """
    # Tabulating intersection tool in ArcGIS (gives the area/percentage of two overlapping features) in ArcGIS
    intersect_iris_zone = pd.read_csv(config['input']['tabulate_intersection'],sep=';', dtype={'code_emd' : str, 'CODE_IRIS': str})
    # print(intersect_iris_zone.columns)
    # String to float
    intersect_iris_zone[['AREA', 'PERCENTAGE']] = intersect_iris_zone[['AREA', 'PERCENTAGE']].astype(float)
    # TODO: if correct EMD zone strings in the excel file then this line is not needed
    #intersect_iris_zone['code_emd'] = '0' + intersect_iris_zone['code_emd']
    return intersect_iris_zone

# 2 step
def read_location_of_activity(df):
    """Read location of activity.csv anc check whether all individuals have activity
   HOme or  Home_getaway
   """
    # loc_of_actv = pd.read_csv(config['LOA']['location_of_activity'], dtype={'Home':str})
    loc_of_actv = df
    # detect and print homeless peoples
    loc_of_actv["Home"] = loc_of_actv["Home"].str.split(', ').str[0]
    loc_of_actv["Home_getaway"] = loc_of_actv["Home_getaway"].str.split(', ').str[0]
    homeless_peoples = loc_of_actv[(loc_of_actv['Home'] == '') & (loc_of_actv['Home_getaway'] == '')]
    # print('Homeless peoples:', homeless_peoples)
    homeless_peoples.to_csv(r"output\EMD_to_IRIS\homeless_people.csv")
    return loc_of_actv

# 3 Step
def distribute_people_from_loa_in_iris(location_of_activity, zone_to_iris_mapping):
    '''
    Merge table and group loa by household
    '''
    # print(location_of_activity)
    loa_grouped_by_household = _group_loa_by_household(location_of_activity)
    # the issue of empty EMD of Home was fixed-> if Home is missing then Home_gatweway is taken for joing (the middle lien in the example below)
    '''
    Output:
    sector	sector_fine	sample_id	person_count	Home	Home_getaway	iris_id
    15	    2	        40	        2	                    011011	        672180203
    50	    33	        528	        3	            050033	050035, 050038	671800203
    Number of people 10216
    -> take Home_gatwway to Home
    15	    2	        40	        2	            011011	 011011
    '''
    # group loa by 'Home' located in EMD zones
    loa_grouped_by_home_zone = _group_loa_by_home_zone(loa_grouped_by_household)
    '''
        Output:
        Home	persons_EMD
        01004	20
    '''
    # Merge two tables
    zone_to_iris_mapping = pd.merge(zone_to_iris_mapping, loa_grouped_by_home_zone, how='left', left_on='code_emd',
                                    right_on='Home').fillna(0)
    zone_to_iris_mapping = zone_to_iris_mapping.sort_values(by='PERCENTAGE', ascending=False)
    """
    output:
    OBJECTID	nom_commun	code_emd	NOM_COM	    CODE_IRIS	AREA	    PERCENTAGE	    Home	persons_EMD
    1	        Achenheim	2001	    Achenheim	670010000	4456004.597	89.67908717	    0	         0
    Number of people 10213
    """
    # TODO: sort percentage ascending (see example EMD 063001) <- done

    # Ditribute total person_count to IRIS based on rounding up approach
    people_left = {}
    zone_to_iris_mapping["persons_IRIS"] = \
        zone_to_iris_mapping.apply(
            lambda row: distribute_people_in_iris(people_left, row['Home'], row['persons_EMD'], row['PERCENTAGE']),
            axis=1)
    '''
    OBJECTID	nom_commun	code_emd	NOM_COM	    CODE_IRIS	AREA	    PERCENTAGE	Home	persons_EMD	persons_IRIS
        75	    Artolsheim	63001	    Artolsheim	670110000	10952462.38	    97.26	063001	    19	    18
        76	    Artolsheim	063001	    Boesenbiesen670530000	1891.39	        0.02	063001	    19	    1
        77	    Artolsheim	063001	    Bootzheim	670560000	20776.87	    0.18	063001	    19	    0
    Number of people in EMD:10213, IRIS: 10187
    '''
    # TODO: replace hard coded path- > CONFIG.txt
    zone_to_iris_mapping.sort_values(by='code_emd').to_csv(r".\output\EMD_to_IRIS\Zone_Iris_Mapping.csv")
    zone_to_iris_mapping.to_excel(r".\output\EMD_to_IRIS\Zone_Iris_Mapping.xlsx", sheet_name='Zone_Iris_Mapping',
                                  index=False)

    # Prepare dict for distributing people with their housholds in iris_zones
    mapper = Zone_to_Iris_Mapper()
    zone_to_iris_mapping.apply(lambda row: mapper.add_mapping(row['Home'], row['CODE_IRIS'], row['persons_IRIS']), axis=1)
    mapper.prepare_distribution() # build empty dict

    # Sort houshold by  person_count ascending
    loa_grouped_by_household.sort_values(by='person_count')

    # Prepare data frame for distributing persons in iris
    loa_grouped_by_household['iris_id'] = loa_grouped_by_household.apply(
        lambda row: mapper.map_house_zone_to_iris(row['Home'], row['Home_getaway'], row['person_count']), axis=1)
    '''
    sector	sector_fine	sample_id	person_count	Home	Home_getaway
    1	    4	        18	        4	            001004	
    '''
    #loa_grouped_by_household.to_csv(r".\output\EMD_to_IRIS\loa_grouped_by_houses.csv")
    loa_house_to_iris_map = House_to_iris_map()
    loa_house_to_iris_map.init_from_df(loa_grouped_by_household)
    return loa_house_to_iris_map

def _group_loa_by_household(location_of_activity):
    household_key = ['sector', 'sector_fine', 'sample_id']
    # group loa by houses
    loa_grouped_by_houses = location_of_activity.drop_duplicates(subset=['sector', 'sector_fine', 'sample_id', 'person_id']).groupby(household_key)

    loa_grouped_by_houses = loa_grouped_by_houses.agg({'person_id': ['count']})
    loa_grouped_by_houses.reset_index(drop=False, inplace=True)
    # get rid of multiindex
    loa_grouped_by_houses.columns = ['_'.join(tup).rstrip('_') for tup in loa_grouped_by_houses.columns.values]

    loa_grouped_by_houses.drop_duplicates(subset=household_key)
    loa_grouped_by_houses = loa_grouped_by_houses.rename(columns={'person_id_count': 'person_count'})
    loa_grouped_by_houses = pd.merge(loa_grouped_by_houses, location_of_activity.drop_duplicates(subset=household_key),
                                     how='left', on=household_key)
    loa_grouped_by_houses = loa_grouped_by_houses[
        ['sector', 'sector_fine', 'sample_id', 'person_count', 'Home', 'Home_getaway']]
    # Take Home_getaway if EMD of Home is missing-> in the mext this table will be joined with the zone_to_iris using Home column
    # loa_grouped_by_houses["Home"] = loa_grouped_by_houses["Home"].str.split(', ').str[0]
    # loa_grouped_by_houses["Home_getaway"] = loa_grouped_by_houses["Home_getaway"].str.split(', ').str[0]
    # use Home_getaway is Home is not there
    loa_grouped_by_houses["Home"] = loa_grouped_by_houses.apply(lambda row: row['Home_getaway'] if row['Home'] == '' else row['Home'], axis=1)
    '''
    Output:
    sector	sector_fine	sample_id	person_count	Home	Home_getaway	iris_id
    10	    5	        27	        3	            010005	010005	        673890000
    15	    2	        40	        2	                    011011	        672180203
    50	    33	        528	        3	            050033	050035, 050038	671800203
        
    '''
    # TODO: convert hard coded path to CONFIG.txt
    # loa_grouped_by_houses.to_csv(".\output\EMD_to_IRIS\loa_grouped_by_houses.csv")
    # loa_grouped_by_houses.to_excel(r".\output\EMD_to_IRIS\loa_grouped_by_houses.xlsx",
    #                                sheet_name='loa_grouped_by_houses',
    #                                index=False)
    return loa_grouped_by_houses

def _group_loa_by_home_zone(loa_grouped_by_houses):
    '''Count all individuals of Home activity'''
    # group loa by 'Home'
    loa_grouped_by_home_zone = loa_grouped_by_houses.groupby('Home').agg({'person_count': ['sum']})
    loa_grouped_by_home_zone.reset_index(drop=False, inplace=True)

    # this is needed to get rid of multiindex
    loa_grouped_by_home_zone.columns = ['_'.join(tup).rstrip('_') for tup in loa_grouped_by_home_zone.columns.values]
    # rename column
    loa_grouped_by_home_zone = loa_grouped_by_home_zone.rename(columns={'person_count_sum': 'persons_EMD'})
    '''
    Output:
    Home	persons_EMD
    1004	20
    '''
    # loa_grouped_by_home_zone.to_csv('.\output\EMD_to_IRIS\loa_grouped_by_home_zone.csv')
    return loa_grouped_by_home_zone

def distribute_people_in_iris(people_to_distribute, zone_id, max_in_zone, percentage):
    ''' Distribute individuals from Home (origin EMD zone)
    starting based on rounding up the number of individuals
    derived from the perctange of EMD zone within IRIS zone.
    '''
    if not zone_id in people_to_distribute.keys():
        people_to_distribute[zone_id] = (max_in_zone, 0.0)
    if people_to_distribute[zone_id][0] <= 0 :
        return 0
    # With ceiling only round to the next intiger
    # The floor() method returns the floor of x i.e. the largest integer not greater than x
    # distributed_people = math.ceil(max_in_zone * (percentage / 100.00))
    # rounding with ceiling from +0.5
    distributed_people = math.floor(max_in_zone * (percentage / 100.00) + 0.5)

    # this can happen because of ceiling
    if distributed_people > max_in_zone:
        distributed_people = max_in_zone
    # this happen also because of ceiling. Rounding up  when no people left to distribute
    if distributed_people > people_to_distribute[zone_id][0]:
        distributed_people = people_to_distribute[zone_id][0]
    elif distributed_people == 0 and people_to_distribute[zone_id][0] > 0:
        # If  there are some people left (mostly one)
        distributed_people = people_to_distribute[zone_id][0]
    #last zone - distribute rest
    elif (people_to_distribute[zone_id][1] + percentage) >= 99.9:
        # last man in the zone
        distributed_people =  people_to_distribute[zone_id][0]
    people_to_distribute[zone_id] = (people_to_distribute[zone_id][0] - distributed_people, people_to_distribute[zone_id][1] + percentage)

    #TODO: check whether the person_EMD =sum of person_IRIS (ex. 018008, 052117)
    return distributed_people

def add_home(home_zones, row):
    home_zones[(row['sector'], row['sector_fine'], row['sample_id'])] = row['Home']

def get_home(home_zones, home_without_activity, row):
    key = (row['sector'], row['sector_fine'], row['sample_id'])
    if key in home_zones.keys():
        return home_zones[key]
    else:
        home_without_activity[key] = 1
        return 0

def distribution_activity_trips_emd_to_iris(df):

    # 1: Get mapping of zone to iris with percentage coverage
    zone_to_iris_mapping = zone_to_iris()
    # 2: Read activity_chain
    location_of_activity = read_location_of_activity(df)
    # 3: Merge both table (#1 & #2) and distribute people activity "homes" in iris and prepare an empty dataframe for further steps
    loa_house_to_iris_map = distribute_people_from_loa_in_iris(location_of_activity, zone_to_iris_mapping)

    # 4: Get IRIS id for Home activity for all columns identifing sampled individuals
    location_of_activity['Home_iris_id'] = location_of_activity.apply(
        lambda row: loa_house_to_iris_map.get_iris_id(row['sector'], row['sector_fine'], row['sample_id']), axis=1)

    ## 5 Add iris chains to loa (Replace EMD based activity chain by IRIS-based activity chain)
    zone_chain_mapper = Zone_Chain_Mapper(loa_house_to_iris_map, zone_to_iris_mapping)
    location_of_activity['iris_chain'] = location_of_activity.apply(
        lambda row: zone_chain_mapper.map_chain_to_iris_chain(row['sector'], row['sector_fine'], row['sample_id'],
                                                              row['zone_chain']), axis=1)
    # TODO: replce hard coded path- > CONFIG.txt
    location_of_activity.to_csv(r".\output\EMD_to_IRIS\location_of_activity_iris.csv")
    #location_of_activity.to_excel(r".\output\EMD_to_IRIS\location_of_activity_iris.xlsx", sheet_name='loc_to_iris',
    #                              index=False)

    print('EMD zone to IRIS zone done')
    return  location_of_activity

if __name__ == '__main__':
    distribution_activity_trips_emd_to_iris()

