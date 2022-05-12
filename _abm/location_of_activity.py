import emd_to_iris
from distance_between import _get_distance_random_points, _get_euclidean_distance_zone, \
    _get_euclidean_distance_iris
from prepare_emd import _prepare_emd
from time_of_day import *
# change the root directory to where CONFIG is kept
from time_of_day import _generate_time

config = configparser.ConfigParser()
os.chdir(os.path.dirname(sys.path[0]))
config.read(r'CONFIG.txt')
time_df, activity_time_df, tour_time_df, trip_time_df = _generate_time()

# Converting the variables to its maximum value
etablissement_variables = {'NN': 1,
                           '00': 0,
                           '01': 2,
                           '02': 5,
                           '03': 9,
                           '11': 19,
                           '12': 49,
                           '21': 99,
                           '22': 199,
                           '31': 249,
                           '32': 499,
                           '41': 999,
                           '42': 1999,
                           '51': 4999,
                           '52': 9999,
                           '53': 19999,}

def dataset_activity_wise(df: pd.DataFrame, chain: str, file_name: str):
    """
    this function divides the dataframe activity wise based on primary activity and modifies the dataframes so that it
    can be used for MNL
    @param df: dataframe that needs to divided activity wise based on primary activity
    @param chain: type of chain (activity, tour, trip)
    @param file_name: file name
    @return: the modified dataframe
    """
    # finding out the main activity by sorting the list of activities
    # and getting the activity at the first position
    # df['primary_activity'] = df[chain + '_chain'].apply(
    #     lambda x: '>'.join(sorted(x.split('>'), key=lambda val: hierarchy_order[val]))).str.split('>').str[0]
    df['intermediate'] = df[chain + '_chain'].apply(lambda x: ','.join(x.split('>')[1:-1]))
    df, values = chain_dict_segregation(df, chain + '_chain', chain + '_iris_chain', '>')
    for col in df.columns:
        if col in [*hierarchy_order]:
            df.rename(columns={col: col + '_iris'}, inplace=True)
    df, values = chain_dict_segregation(df, chain + '_chain', chain + '_zone_chain', '>')
    for col in df.columns:
        if col in [*hierarchy_order]:
            df.rename(columns={col: col + '_zone'}, inplace=True)
    # Making datasets of each primary activity in a csv format
    for k, v in hierarchy_order.items():
        df[df['intermediate'].str.contains(k)].to_csv(
            config['LOA']['datasets'] + '/' + k + '/' + file_name + '_' + k + '.csv', index=False)
    modify_dataset_for_MNL(config['input']['work_size'],
                           config['LOA']['datasets']  + '/' + 'Work' + '/' + file_name + '_' + 'Work.csv',
                           chain)
    modify_dataset_for_MNL(config['input']['school19_size'],
                           config['LOA']['datasets']  + '/' + 'School' + '/' + file_name + '_' + 'School.csv',
                           chain)
    modify_dataset_for_MNL(config['input']['university19_size'],
                           config['LOA']['datasets']  + '/' + 'University' + '/' + file_name + '_' + 'University.csv',
                           chain)
    modify_dataset_for_MNL(config['input']['shopping19_size'],
                           config['LOA']['datasets'] + '/' + 'Shopping' + '/' + file_name + '_' + 'Shopping.csv',
                           chain)
    modify_dataset_for_MNL(config['input']['leisure19_size'],
                           config['LOA']['datasets'] + '/' + 'Leisure' + '/' + file_name + '_' + 'Leisure.csv',
                           chain)
    modify_dataset_for_MNL(config['input']['home_size'],
                           config['LOA']['datasets'] + '/' + 'Home' + '/' + file_name + '_' + 'Home.csv',
                           chain)
    modify_dataset_for_MNL(config['input']['home_getaway_size'],
                           config['LOA']['datasets'] + '/' + 'Home_getaway' + '/' + file_name + '_' + 'Home_getaway.csv',
                           chain)
    return df

def modify_dataset_for_MNL(size_with_iris: str, file_name: str, chain: str):
    activity = ''
    for i in hierarchy_order:
        if i in file_name:
            activity = i
    if activity in file_name:
        print('Modifying ' + file_name + ' started')
        # Work as Primary Destination Choice
        size = pd.read_csv(size_with_iris,dtype={'DCOMIRIS': str})
        # converting the variables using the dictionary
        if activity == 'Work':
            size['size'] = size['size'].astype(str).map(etablissement_variables)
        else:
            size['size'] = size['size'].astype(int).astype(str)
        # finding the sum and not the mean (different from Jordan's thesis)
        size = size.groupby('DCOMIRIS')['size'].sum()
        # searches for the dictionary to find the size
        def get_size(row):
            row = stringlist_to_list(row)
            size_dict = size.to_dict()
            for iris, nb in size_dict.items():
                if str(iris) in row:
                    return str(iris), nb
        df = pd.read_csv(file_name)
        # starting home loa
        # finds the previous indices of activities and the activities of the selected 'activity' and makes a chain
        df['previous'] = df[chain + '_chain'].apply(
            lambda row: '|'.join([row.split('>')[index - 1] for index, value in enumerate(row.split('>')) if value == activity]))
        # finds the previous indices of activities and the activities' iris of the selected 'activity' and makes a chain
        df['previous_iris'] = df.apply(
            lambda row: '|'.join([row[chain + '_iris_chain'].split('>')[index - 1]
                                  for index, value in enumerate(row[chain + '_chain'].split('>'))
                                  if value == activity]),
            axis=1)
        df['previous_zone'] = df.apply(
            lambda row: '|'.join([row[chain + '_zone_chain'].split('>')[index - 1]
                                  for index, value in enumerate(row[chain + '_chain'].split('>'))
                                  if value == activity]),
            axis=1)
        # the iris of that activity that was chosen
        df['current_iris'] = df[activity + '_iris'].apply(lambda row: '|'.join(stringlist_to_list(row)))
        df['current_zone'] = df[activity + '_zone'].apply(lambda row: '|'.join(stringlist_to_list(row)))
        df = df.astype(str).apply(lambda row: row.str.split('|').explode()).reset_index(drop = True)
        df['distance_iris'] = df.apply(
            lambda row: _get_euclidean_distance_iris(row['current_iris'], row['previous_iris']),
            axis=1)
        df['distance_zone'] = df.apply(
            lambda row: _get_euclidean_distance_zone(row['current_zone'], row['previous_zone']),
            axis=1)
        df['random_distance_zone'] = df.apply(
            lambda row: _get_distance_random_points(row['current_zone'], row['previous_zone']),
            axis=1)
        activity_count(df, 'previous')
        df['size'] = df['current_iris'].apply(lambda row: get_size(row)).str[1]
        df[['size']] = df[['size']].fillna(0)
        df.to_csv(file_name)
        print('Modifying ' + file_name + ' finished')

# Not used
def add_size_distance(size_with_iris: str, file_name: str):
    """
    this function helps in adding the distance information between the origin and destination iris and the size of
    attraction information of the particular activity. Generates the modified datasets (csv) produced by
    _generate_location_chains function.
    @param size_with_iris: data on the size/magnitude of attraction of the particular activity
    @param file_name: the particular activity
    """
    activity = ''
    for i in hierarchy_order:
        if i in file_name:
            activity = i
    print(activity)
    if activity in file_name:
        print('Modifying ' + file_name + ' started')
        size = pd.read_csv(size_with_iris, dtype = {'DCOMIRIS': str})
        # converting the variables using the dictionary
        if activity == 'Work':
            size['size'] = size['size'].astype(str).map(etablissement_variables)
        elif activity == 'Shopping':
            size['size'] = size['size'] * 53
        elif activity == 'School' or activity == 'University':
            size['size'] = size['size'].astype(int).astype(str)
        # finding the sum and not the mean (different from Jordan's thesis)
        size = size.groupby('DCOMIRIS')['size'].sum()
        # searches for the dictionary to find the size
        def get_size(row):
            row = stringlist_to_list(row)
            size_dict = size.to_dict()
            for iris, nb in size_dict.items():
                if str(iris) in row:
                    return str(iris), nb
        df = pd.read_csv(file_name)
        # starting home loa
        df['user_home'] = df['Home'].apply(
            lambda row: stringlist_to_list(row)[0]).astype(float).fillna(0).astype('Int64').astype('str')
        # the activity that whose iris had the size data was chosen
        df['activity_chosen'] = df[activity + '_iris'].apply(lambda row: get_size(row)).str[0]
        df['size'] = df[activity].apply(lambda row: get_size(row)).str[1]
        df['distance'] = df.apply(
            lambda row: _get_euclidean_distance_iris(row['user_home'], row['activity_chosen']),
            axis = 1)
        df.to_csv(file_name)
        print('Modifying ' + file_name + ' finished')

# Not used
def zone_to_iris():
    """
    this function reads the area|percentage file created by any GIS app that shows overlapping area and its percentage
    overlap between survey zone feature and contour iris feature. This helps in generating a zone to iris conversion
    sheet
    """
    # Tabulating intersection tool in ArcGIS (gives the area/percentage of two overlapping features) in ArcGIS
    df = pd.read_csv(config['input']['area_percentage'])
    df['code_sec_1'] = df['code_sec_1'].astype(str).str.zfill(6)
    # String to float
    df[['AREA', 'PERCENTAGE']] = df[['AREA', 'PERCENTAGE']].astype(float)
    iris_list = df['DCOMIRIS'].unique()
    overlapped_df = df.sort_values(
        by = 'PERCENTAGE', ascending = False).drop_duplicates('code_sec_1').sort_index().astype(str)
    overlapped_iris_list = overlapped_df['DCOMIRIS'].unique()
    missing_iris = list(set(iris_list).difference(overlapped_iris_list))
    zone_missing_iris = []
    # sorts the column values based on percentage and keeps the row with the maximum percentage, removes irises
    for iris in missing_iris:
        missing_row = df[df['DCOMIRIS'].astype(int) == iris].astype(str)
        # missing_row['code_sec_1'] = missing_row['code_sec_1'].apply(lambda row: str(row) + '_')
        missing_row = missing_row.sort_values(
            by = 'PERCENTAGE', ascending = False).drop_duplicates('DCOMIRIS').sort_index()
        overlapped_df = pd.concat([overlapped_df, missing_row])
        missing_row['code_sec_1'].apply(lambda row: zone_missing_iris.append(row))
    overlapped_df.to_csv(config['ZoneIris']['zone_to_iris'])
    return overlapped_df

def find_distance(iris_trip_chain: str):
    """
    this function takes the iris_trip_chain as input and converts each of them to their trip distance
    @param iris_trip_chain: the chain of irises like a trip (671300102>674822204|674822204>671300102)
    @return: the distance between each iris trip (18.25|18.25)
    """
    lis = iris_trip_chain.split('|')
    new_lis = []
    for i in lis:
        iris_1 = i.split('>')[0]
        iris_2 = i.split('>')[-1]
        # print(iris_1, iris_2, type(iris_1), type(iris_2))
        new_lis.append(str(_get_euclidean_distance_iris(iris_1, iris_2)))
    return '|'.join(new_lis)

def _generate_location():
    """
    this function gets the survey data (cleaned) from the prepare_emd.py and generates each activity dataset (csv)
    along with one main location_of_activity dataset. These datasets not only contain the information from time_of_day
    dataframe but also the information on iris_chain (sequence of locations of activities), zone_chain,
    distance between consecutive irises|zone and magnitude/size of attraction of the concerned activity.
    @return: returns all of the four datasets with their location chains as a dataframes which comprises of all chains,
    activity chains, tour chains, and trip chains respectively
    """
    hh_people, location_df = _prepare_emd()

    ######################################################
    ###### ZONE TO IRIS using zone_to_iris() method ######
    ######################################################
    # replacer = zone_to_iris().set_index('code_sec_1')['DCOMIRIS'].to_dict()
    # location_df[zones.columns] = zones.replace(replacer)
    # location_df[['o_zone', 'd_zone']] = location_df[zones.columns].values
    # zones = location_df.filter(like = '_zone').copy()
    # irises = location_df.filter(like = '_iris').copy()
    # location_df[zones.columns] = location_df[zones.columns].astype(str).applymap(lambda row: str(int(row)))
    # location_df[irises.columns] = location_df[irises.columns].astype(str)
    # location_df = location_df.rename(columns = {'origin_zone': 'origin_iris', 'destination_zone': 'destination_iris'})
    # all = len(location_df)
    # location_df = location_df[(location_df['origin_iris'] > 1000000) & (location_df['destination_iris'] > 1000000)]
    # inside = len(location_df)
    # print('The number of trip locations (iris) outside Bas Rhin are: ',
    #       all - inside, ' out of ', all)
    # location_df = location_df.groupby([*grouping_pid,
    #                                    *personal_attributes])[
    #     ['origin_iris', 'o_zone','destination_iris',
    #      'origin_motive', 'd_zone', 'destination_motive',
    #      'origin_actual_motive', 'destination_actual_motive']].agg('>'.join)
    # location_df['iris_chain'] = location_df.origin_iris + '>' + \
    #                             location_df.destination_iris.str.rsplit('>', 1).str[1]
    # location_df['zone_chain'] = location_df.o_zone + '>' + \
    #                             location_df.d_zone.str.rsplit('>', 1).str[1]

    location_df.to_csv(config['LOA']['ungrouped'], index = False)

    ######################################################
    ###### ZONE TO IRIS using emd_to_iris.py script ######
    ######################################################
    location_df = location_df.groupby([*grouping_pid,*personal_attributes])[
        ['origin_zone', 'destination_zone',
        'origin_motive', 'destination_motive',
        'origin_actual_motive', 'destination_actual_motive']].agg('>'.join)
    location_df = pd.merge(location_df, activity_time_df, on = [*grouping_pid, *personal_attributes], how = 'left')
    # making the index of the dataframe to columns
    location_df.reset_index(level = location_df.index.names, inplace = True)
    print('Added the socio-economic attributes to the dataset')
    location_df['activity_chain'] = location_df.origin_motive + '>' + \
                                    location_df.destination_motive.str.rsplit('>', 1).str[1]
    # the activity_chain in actual numeric form
    location_df['activity_actual_chain'] = location_df.origin_actual_motive + '>' + \
                                           location_df.destination_actual_motive.str.rsplit('>', 1).str[1]
    location_df['zone_chain'] = location_df.origin_zone + '>' + \
                                location_df.destination_zone.str.rsplit('>', 1).str[1]
    location_df, values = chain_dict_segregation(location_df.applymap(str), 'activity_chain', 'zone_chain', '>')
    # Split EMD to IRIS zones
    location_df["Home"] = location_df["Home"].str.split(', ').str[0]
    location_df["Home_getaway"] = location_df["Home_getaway"].str.split(', ').str[0]
    # Removing the non-Home based tours
    # getting the first activity from the list of activities
    location_df['first_activity'] = location_df['activity_chain'].str.split('>').str[0]
    # removing activities that don't start from home
    location_df = location_df[location_df['first_activity'].isin(home_activity)]
    # getting the last activity from the list of activities
    location_df['last_activity'] = location_df['activity_chain'].str.split('>').str[-1]
    # removing activity that don't end at home
    location_df = location_df[location_df['last_activity'].isin(home_activity)]
    # zone to iris using emd_to_iris.py
    emd_to_iris.distribution_activity_trips_emd_to_iris(location_df)
    location_df.drop(columns = ['first_activity',
                                'last_activity'], inplace = True)
    # A complete dataset with all the data in csv format
    location_df.drop(location_df.filter(regex = '(o_|d_|origin|destination|duration|actual)').columns, axis = 1, inplace = True)

    '''
    ACTIVITY_CHAIN with time chains and location chains (iris and EMD zone)
    '''
    activity_location_df = location_df.copy()
    # renames them according to the chain type
    activity_location_df = activity_location_df.rename(
        columns = {'iris_chain': 'activity_iris_chain', 'zone_chain': 'activity_zone_chain'})
    activity_location_df.drop(activity_location_df.filter(regex = '(departure|arrival)').columns, axis = 1, inplace = True)
    activity_location_df = dataset_activity_wise(activity_location_df, 'activity', 'activity_non_condensed_location')
    activity_location_df.to_csv(config['LOA']['datasets'] + 'activity_non_condensed_location_df.csv', index = False)


    '''
    TOUR_CHAIN with time chains and location chains (iris and EMD zone)
    '''
    location_df['tour_chain'] = location_df['activity_chain'].astype(str).apply(make_tour)
    location_df['tour_rank'] = location_df['tour_chain'].apply(
        lambda row: '|'.join([str(i) for i in get_position_list(row.split('|'))]))
    location_df['tour_time_chain'] = location_df.astype(str).apply(
        lambda row: make_chain_on_reference(row['tour_chain'], row['activity_time_chain']), axis = 1)
    location_df['tour_iris_chain'] = location_df.astype(str).apply(
        lambda row: make_chain_on_reference(row['tour_chain'], row['iris_chain']), axis = 1)
    location_df['tour_zone_chain'] = location_df.astype(str).apply(
        lambda row: make_chain_on_reference(row['tour_chain'], row['zone_chain']), axis = 1)
    # generating the new tours as new rows keeping the same attributes
    tour_location_df = location_df.astype(str).apply(lambda row: row.str.split('|').explode()).reset_index(drop = True)
    tour_location_df['tour_time_chain'] = tour_location_df['tour_time_chain'].apply(
        lambda row: row[:-1] if row[-1] == '>' else row)
    tour_location_df['tour_iris_chain'] = tour_location_df['tour_iris_chain'].apply(
        lambda row: row[:-1] + '>' + row.split('>')[0] if row[-1] == '>' else row)
    tour_location_df['tour_zone_chain'] = tour_location_df['tour_zone_chain'].apply(
        lambda row: row[:-1] + '>' + row.split('>')[0] if row[-1] == '>' else row)
    tour_location_df['tour_chain_rank'] = tour_location_df['tour_chain'] + tour_location_df['tour_rank']
    # removes previous unnecessary chains
    tour_location_df = tour_location_df.drop(columns = ['iris_chain', 'zone_chain'])
    tour_location_df.drop(tour_location_df.filter(regex = 'activity').columns, axis = 1, inplace = True)
    tour_location_df = dataset_activity_wise(tour_location_df, 'tour', 'tour_non_condensed_location')
    tour_location_df.to_csv(config['LOA']['datasets'] + 'tour_non_condensed_location_df.csv', index = False)
    location_df.drop(location_df.filter(regex = 'tour').columns, axis = 1, inplace = True)


    '''
    TRIP_CHAIN with time chains and location chains (iris and EMD zone)
    '''
    location_df['trip_chain'] = location_df['activity_chain'].apply(make_trip)
    location_df['trip_time_chain'] = location_df.apply(
        lambda row: make_chain_on_reference(row['trip_chain'], row['activity_time_chain']), axis = 1)
    location_df['trip_iris_chain'] = location_df['iris_chain'].apply(make_trip)
    location_df['trip_zone_chain'] = location_df['zone_chain'].apply(make_trip)
    trip_location_df = location_df.astype(str).apply(lambda row: row.str.split('|').explode()).reset_index(drop = True)
    # trip_location_df = location_df.assign(
    #     trip_time_chain = location_df.trip_time_chain.str.split('|')).explode('trip_time_chain').reset_index(drop = True)
    trip_location_df['trip_time_chain'] = trip_location_df['trip_time_chain'].apply(
        lambda row: row[:-1] if row[-1] == '>' else row)
    # removes previous unnecessary chains
    trip_location_df = trip_location_df.drop(columns = ['iris_chain', 'zone_chain'])
    trip_location_df.drop(trip_location_df.filter(regex = 'activity').columns, axis = 1, inplace = True)
    # trip_location_df = dataset_activity_wise(trip_location_df, 'trip', 'trip_non_condensed_location')
    trip_location_df.to_csv(config['LOA']['datasets'] + 'trip_non_condensed_location_df.csv', index = False)
    print('Generated the iris dataset for each primary activity in a csv format')
    print('-----all location-of-activity datasets were successfully generated-----')

    # A complete dataset with all the data in csv format
    # adding all the information in the general file
    location_df = location_df.rename(
        columns = {'iris_chain': 'activity_iris_chain', 'zone_chain': 'activity_zone_chain'})
    location_df['distance_chain'] = location_df['activity_iris_chain'].astype(str).apply(make_trip).apply(find_distance)
    location_df['tour_chain'] = location_df['activity_chain'].astype(str).apply(make_tour)
    location_df['tour_time_chain'] = location_df.astype(str).apply(
        lambda row: make_chain_on_reference(row['tour_chain'], row['activity_time_chain']), axis=1)
    location_df['tour_iris_chain'] = location_df.astype(str).apply(
        lambda row: make_chain_on_reference(row['tour_chain'], row['activity_iris_chain']), axis=1)
    location_df['tour_zone_chain'] = location_df.astype(str).apply(
        lambda row: make_chain_on_reference(row['tour_chain'], row['activity_zone_chain']), axis=1)
    location_df.to_csv(config['LOA']['location_of_activity'], index = False)

    return location_df, activity_location_df, tour_location_df, trip_location_df

if __name__ == '__main__':
    _generate_location()

