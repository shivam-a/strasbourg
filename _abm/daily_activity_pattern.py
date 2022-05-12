import configparser
import os
import sys
import pandas as pd
from prepare_emd import _prepare_emd, grouping_pid, grouping
config = configparser.ConfigParser()
# change the root directory to where CONFIG is kept
os.chdir(os.path.dirname(sys.path[0]))
config.read(r'CONFIG.txt')

# hierarchy of activities
hierarchy_order = {'Work': 0,
                   'School': 1,
                   'University': 2,
                   'Shopping': 3,
                   'Leisure': 4,
                   'Accompany': 5,
                   'Other': 6,
                   'Home': 7,
                   'Home_getaway': 8}
# independent socio-economic variables
personal_attributes = ['sex', 'age', 'enrollment', 'license', 'occupation']
household_attributes = ['hh_income', 'hh_capacity']
socio_economic_attributes = [*personal_attributes, *household_attributes]
# according to the EMD there are two types of home activities
home_activity = ['Home', 'Home_getaway']

def make_tour(activity_chain: str):
    """
    this function makes tour_chain on an activity_chain separated by '|'
    @param activity_chain: the activity_chain that needs to made into a tour format
    @return: tour_chain
    """
    # first and last activity of activity_chain
    first_activity = activity_chain.split('>')[0]
    # last_activity = chain_type.split('>')[-1]
    new_tour_list = []
    tour_list = activity_chain.split('>' + first_activity + '>')
    for tour in tour_list:
        position = tour_list.index(tour)
        last_position = len(tour_list) - 1
        if tour == 'Home':
            tour = 'Home_getaway>' + tour
        elif tour == 'Home_getaway':
            tour = 'Home>' + tour
        new_tour_list.append(make_home_based(tour, first_activity, position, last_position))
    return '|'.join(new_tour_list)

def make_trip(activity_chain):
    """
    this function makes trip_chain on an activity_chain separated by '|'
    @param activity_chain: the activity_chain that needs to made into a trip format
    @return: trip_chain
    """
    activity_list = activity_chain.split('>')
    trip_chain = ''
    for index in range(len(activity_list) - 1):
        trip_chain = trip_chain + '|' + activity_list[index] + '>' + activity_list[index + 1]
    return trip_chain[1:]

# adds Home to activity_chain wherever missing
def make_home_based(tour: str, additive: str, position: int, last_position: int):
    """
    this function makes any tour into home-based tour_chain by concatenating home_activity either at the start,
    end or both ends of the chain (refer to issue #10 on gitlab)
    @param tour: the chain that needs to be modified
    @param additive: the first activity of the activity chain
    @param position: position of tour in the tour_list
    @param last_position: last position of the tour in tour_list
    @return: home_based tour_chain
    """
    # first and last activity of tour_chain
    first_activity = tour.split('>')[0]
    last_activity =  tour.split('>')[-1]
    if first_activity in home_activity and last_activity in home_activity:
        tour = tour
        if tour == 'Home>Home_getaway' and position != last_position:
            tour = 'Home>Home_getaway>Home'
        elif tour == 'Home_getaway>Home' and position != last_position:
            tour = 'Home>Home'
    elif first_activity in home_activity and last_activity not in home_activity:
        tour = tour + '>' + first_activity
    elif last_activity in home_activity and first_activity not in home_activity:
        tour = last_activity + '>' + tour
    else:
        tour = additive + '>' + tour + '>' + additive
    return tour

def get_position_list(lis: list):
    """
    this function returns a list with the position of each element
    @param lis: the list of elements
    @return: position of each element in the list as a list
    """
    return [i+1 for i in range(len(lis))]

# total number of each activities in the activity_chain
def activity_count(df: pd.DataFrame, chain: str):
    """
    this function will make activity columns in the dataframe (input) that will describe the frequency of that
    particular activity's occurrence in the chain
    @param df: the dataframe that wants to add activity columns giving the frequency of each activity occurring the chain
    @param chain: the chain that needs to be examined
    """
    for activity in hierarchy_order.keys():
        # activity_name = 'nb_work' activity = 'Work'
        activity_name = chain + '_' + activity.lower()
        df[activity_name] = df[chain].apply(lambda x: x.split('>').count(activity))
    print('Added columns with the count of each activity in the chain')

def _generate_chain():
    """
    this function gets the survey data (cleaned) from the prepare_emd.py and generates three types of datasets (csv)
    based on the chain type (activity, tour, trip). The datasets contain dependent socio-economic variables and the
    chain as the independent variable.
    @return: returns all of the four datasets as a dataframes which comprises of all chains, activity chains, tour chains,
    and trip chains respectively
    """
    # all attributes unmerged
    persons_households, chain_df = _prepare_emd()
    chain_df.to_csv(config['DAP']['ungrouped'], index=False)
    # chain_df.to_csv(config['DAP']['ungrouped'], index=False)
    # working with activities (dap - daily activity pattern)
    # grouping rows and adding persons characteristics
    chain_df = chain_df.groupby([*grouping_pid,
                     *personal_attributes])[
        ['origin_motive', 'destination_motive', 'origin_actual_motive', 'destination_actual_motive']].agg('>'.join)
    print('Aggregated the origin and destination activities into chains')
    # making the index of the dataframe to columns
    chain_df.reset_index(level=chain_df.index.names, inplace=True)
    def add_hh_capacity(p_hh: pd.DataFrame):
        """
        this function adds the hh_capacity variable to the dataframe
        @param p_hh: the dataframe that requires hh_capacity
        @return: the modified dataframe
        """
        # grouping on the basis of these 4 columns to get household capacity
        p_hh = p_hh.groupby(['sector',
                             'sector_fine',
                             'sample_id',
                             'hh_income'])['person_id'].count().reset_index()
        p_hh['hh_capacity'] = p_hh['person_id']
        p_hh.drop(columns=['person_id'], inplace=True)
        return p_hh
    # adding other household characteristics to dap
    household_char = add_hh_capacity(persons_households)
    print('Added the socio-economic attributes to the dataset')
    # removing the blank rows
    household_char = household_char.dropna()
    # merging the calculated household capacity, income with the dap
    chain_df = pd.merge(chain_df, household_char, on=grouping, how='left')
    chain_df['activity_chain'] = chain_df.origin_motive + '>' + chain_df.destination_motive.str.rsplit('>', 1).str[1]
    # activities in numeric form
    chain_df['activity_actual_chain'] = chain_df.origin_actual_motive + '>' + \
                                  chain_df.destination_actual_motive.str.rsplit('>', 1).str[1]
    print('Added the column with activity sequences both in numeric and categorical form')
    all_chain_count = len(chain_df)
    # getting the first activity from the list of activities
    chain_df['first_activity'] = chain_df['activity_chain'].str.split('>').str[0]
    # removing activities that don't start from home activity
    chain_df = chain_df[chain_df['first_activity'].isin(home_activity)]
    # getting the last activity from the list of activities
    chain_df['last_activity'] = chain_df['activity_chain'].str.split('>').str[-1]
    # removing activities that don't end at home activity
    chain_df = chain_df[chain_df['last_activity'].isin(home_activity)]
    home_chain_count = len(chain_df)
    print('The number of non-home based activity sequences are: ',
          all_chain_count - home_chain_count, ' out of ', all_chain_count)
    # removing columns
    chain_df.drop(columns=['first_activity', 'last_activity'], inplace=True)
    chain_df.drop(chain_df.filter(regex='(origin|destination)').columns, axis=1, inplace=True)
    # trips per person
    chain_df['nb_trip'] = chain_df['activity_chain'].apply(lambda row: len(str(row).split('>')) - 1)
    # tours per person
    chain_df['nb_tour'] = chain_df['activity_chain'].apply(lambda row: len(str(row).split('>Home>')))
    # Adding the dummy variable for nb_tour
    X = pd.get_dummies(chain_df['nb_tour'], prefix='nb_tour')
    chain_df[X.columns] = X
    chain_df.drop('nb_tour', axis=1, inplace=True)

    '''
    ACTIVITY_CHAIN
    Activity is an event that takes place for a duration of time. An activity_chain may or may not be end at the same 
    activity like a tour. It may comprise of multiple tour_chain. A activity_chain is the most detailed travel pattern 
    of an individual. 
    '''
    activity_chain_df = chain_df.copy()
    # give a household id
    activity_chain_df['hh_id'] = activity_chain_df.groupby(grouping).ngroup()
    # finding the most important motive/activity
    activity_chain_df['primary_activity'] = activity_chain_df['activity_chain'].apply(
        lambda x: '>'.join(sorted(x.split('>'), key=lambda val: hierarchy_order[val]))).str.split('>').str[0]
    activity_chain_df['first_activity'] = activity_chain_df['activity_chain'].str.split('>').str[0]
    activity_chain_df['last_activity'] = activity_chain_df['activity_chain'].str.split('>').str[-1]
    # activity_chain_df['tour_chain'] = activity_chain_df['activity_chain'].apply(make_tour)
    # activity_count(activity_chain_df, 'activity_chain')
    activity_chain_df.to_csv(config['DAP']['datasets'] + 'activity_non_condensed_chain_df.csv', index=False)

    '''
    TOUR_CHAIN
    Tour is a sequence of trips starting and ending at the same activity
    A tour_chain is a sequence of two or more trip_chain
    Extracting tour_chain from the activity_chain by splitting the activity_chain into home-based tours
    Example: Home>Shopping>Home>Leisure>Home>Accompany>Home (activity_chain) to 
    1. Home>Shopping>Home (tour_chain) 
    2. Home>Leisure>Home (tour_chain) 
    3. Home>Accompany>Home (tour_chain) 
    '''
    # chain_df['tour_chain'] = chain_df['activity_chain'].apply(
    # lambda row: '|'.join([make_home_based(chain) for chain in row.split('>Home>')]))
    # make tours as home based
    chain_df['tour_chain'] = chain_df['activity_chain'].apply(make_tour)
    chain_df['tour_rank'] = chain_df['tour_chain'].apply(
        lambda row: '|'.join([str(i) for i in get_position_list(row.split('|'))]))
    print('Made the activity chain to a multiple home based tours')
    # generating the new tours as new rows keeping the same attributes
    tour_chain_df = chain_df.astype(str).apply(lambda row: row.str.split('|').explode()).reset_index(drop=True)
    # give a household id
    tour_chain_df['hh_id'] = tour_chain_df.groupby(grouping).ngroup()
    tour_chain_df['tour_chain_rank'] = tour_chain_df['tour_chain'] + tour_chain_df['tour_rank']
    # dropping unnecessary columns
    tour_chain_df.drop(tour_chain_df.filter(regex='(activity|check)').columns, axis=1, inplace=True)
    # finding the most important motive/activity
    tour_chain_df['primary_activity'] = tour_chain_df['tour_chain'].apply(
        lambda x: '>'.join(sorted(x.split('>'), key=lambda val: hierarchy_order[val]))).str.split('>').str[0]
    # activity_count(tour_chain_df, 'tour_chain')
    tour_chain_df['first_activity'] = tour_chain_df['tour_chain'].str.split('>').str[0]
    tour_chain_df['last_activity'] = tour_chain_df['tour_chain'].str.split('>').str[-1]
    tour_chain_df.to_csv(config['DAP']['datasets'] + 'tour_non_condensed_chain_df.csv', index=False)
    print('Split the activity_chain into separate tours and made a new dataframe with only tours')


    '''
    TRIP_CHAIN
    A trip_chain is the smallest unit of travel from one activity to another
    Extracting trip_chain from the tour_chain by splitting the tour_chain into trip
    Example: Home>Shopping>Leisure>Home (tour_chain) to 
    1. Home>Shopping (trip_chain)
    2. Shopping>Leisure (trip_chain)
    3. Leisure>Home (trip_chain)
    '''
    chain_df['trip_chain'] = chain_df['activity_chain'].apply(make_trip)
    # generating the new trips as new rows keeping the same attributes
    trip_chain_df = chain_df.assign(trip_chain=chain_df['trip_chain'].str.split('|')).explode('trip_chain')
    # give a household id
    trip_chain_df['hh_id'] = trip_chain_df.groupby(grouping).ngroup()
    # dropping unnecessary columns
    trip_chain_df.drop(trip_chain_df.filter(regex=r'(activity|tour|check)').columns, axis=1, inplace=True)
    trip_chain_df.to_csv(config['DAP']['datasets'] + 'trip_non_condensed_chain_df.csv', index=False)
    print('Split the tour_chain into separate trips and made a new dataframe with only trips')
    print('-----all chain type datasets were successfully generated-----')

    return chain_df, activity_chain_df, tour_chain_df, trip_chain_df


if __name__ == '__main__':
    _generate_chain()
