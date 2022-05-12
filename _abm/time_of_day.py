import math
from collections import defaultdict
import numpy as np
from daily_activity_pattern import *
from daily_activity_pattern import _generate_chain
from prepare_emd import _prepare_emd, grouping_pid

# change the root directory to where CONFIG is kept
config = configparser.ConfigParser()
os.chdir(os.path.dirname(sys.path[0]))
config.read(r'CONFIG.txt')
chain_df, activity_df, tour_df, trip_df = _generate_chain()
# remove the first element in each list of a list
def remove_first(list_of_list: list):
    """
    this function takes a list of list and remove the first element in each inner list.
    @param list_of_list: the list to be modified
    """
    for lis in list_of_list:
        for i in range(0, len(lis)):
            if i == 0:
                lis.pop(i)

# remove the last element in each list of a list
def remove_last(list_of_list: list):
    """
    this function takes a list of list and remove the last element in each inner list.
    @param list_of_list: the list to be modified
    """
    for lis in list_of_list:
        lis.pop()

# returns a list of float values
def _split_convert(column: pd.Series, separator: str):
    """
    this function takes a column of a dataframe as a list and splits (by the specified separator) each row into a list,
    making a list of list. This helps in creating a dataframe out of the specified column.

    @param column: column of a dataframe that needs to be made into separate dataframe
    @param separator: chain in each row of the column made by a specific character

    @return: list of list of the column
    """
    return [list(map(float, row.split(separator))) for row in column]

# converts a list representation in string to a list
def stringlist_to_list(stringlist: str):
    """
    this function makes a list representation in string format into an actual string.
    @param stringlist: the list representation in string format
    @return: actual list
    """
    return [i for i in str(stringlist).split(', ') if str(stringlist) != '']

def clean_chain(chain: str, separator: str):
    """
    this function cleans the chain '1800.0|1800.0|nan|nan|nan' to '1800.0|1800.0' meaning removes the nan values and
    keeps only the meaningful part.
    @param chain: Any type of chain value
    @param separator: The character used to form the form the chain
    @return: cleaned up chain
    """
    chain = str(chain).split(separator)
    new_chain = ''
    for string in chain:
        if string != 'nan':
            new_chain = new_chain + separator + string
    return new_chain[1:]

def chain_dict(key_chain: str, value_chain: str, separator: str):
    """
    this function returns a dictionary making the key_chain after splitting as the 'key' and the value_chain after
    splitting as 'value' in a list format. This helps in having multiple values for the same key.
    @param key_chain: the chain/sequence of keys that one wants as columns
    @param value_chain: the chain/sequence of values that one wants rows
    @param separator: the chain is separated by a character
    @return: the dictionary of column as key and [row list] as values
    """
    keys_list = list(dict.fromkeys(key_chain.split(separator)))
    chain_dictionary = defaultdict(list, {key : [] for key in keys_list })
    for i in range(0, len(key_chain.split(separator))):
        key = key_chain.split(separator)[i]
        value = value_chain.split(separator)[i]
        chain_dictionary[key].append(value)
    # to remove duplicates
    # for k, v in chain_dictionary.items():
    #     chain_dictionary[k] = list(dict.fromkeys(v))
    return chain_dictionary

# segregation of dictionary from chain_dict to a dataframe
def chain_dict_segregation(df: pd.DataFrame, key_chain: str, value_chain: str, separator: str):
    """
    this function takes a dataframe, its 'key' column name, 'value' column name and separator as an input and returns
    two dataframes, one is the modified of original dataframe and the second dataframe describing the dictionary of the
    two columns. The basic idea behind this function is to split the 'key' and 'value' column values simultaneously by
    the separator to make the 'key' values as column and 'value' values as its row.
    trip_chain_chain - key_chain: Home>School|School>Home, Home>School|School>Leisure|Leisure>School|School>Home
    trip_duration - value_chain: 1200.0|600.0, 5400.0|120.0|120.0|6000.0
    separator: '|'
    Home>School column would contain 1200.0, 5400.0 as its row value
    School>Home  column would contain 600.0, 6000.0 as its row value
    School>Leisure column would contain 120.0 as its row value
    Leisure>School column would contain 120.0 as its row value
    @param df: the specified dataframe
    @param key_chain: 'key' column name
    @param value_chain: 'value' column name
    @param separator: the special character used to form a sequence/chain
    @return: returns specified but modified dataframe and dataframe with the dictionary
    """
    values = []
    # making the activity as the key and it's irises as the values
    df.copy().apply(lambda row: values.append(
        chain_dict(row[key_chain], row[value_chain], separator)), axis = 1)
    values = pd.DataFrame(values)
    # converts all list (string) representation to string ['16800.0', '13200.0'] -> 16800.0, 13200.0
    values = values.astype(str).applymap(
        lambda row: row.replace('[', '').replace(']', '').replace('\'', '') if row != 'nan' else '')
    # adding it to the dataset
    df = df.reset_index(drop = True).assign(**values)
    return df, values

def alternate_list(list_1: list, list_2: list):
    """
    this function takes two lists as input and returns a third with alternate two elements from both lists added together.
    @param list_1: first list
    @param list_2: second list
    @return: formed list
    """
    result = [None]*(len(list_1))
    for i in range(len(result)):
        result[i] = list_1[0] + '-' + list_2[0]
        list_1.pop(0)
        list_2.pop(0)
    return result


def make_chain_on_reference(reference_chain: str, chain: str):
    """
    this function modifies the modify_chain using the reference of reference_chain. Returns modified chain by placing
    the separator on the same position as the reference_chain.
    Example: Home>School>Home|Home>School>Home to 07:30-07:50>12:30-12:50>|13:30-13:50>17:30-17:50
    @param reference_chain: the chain whose position of separator '|' is replicated on the chain
    @param chain: the chain which modified based on the reference_chain
    @return: the modified chain
    """
    activities = reference_chain.split('>')
    lis_chain = chain.split('>')
    pos = []
    c = 0
    for i in range(len(activities)):
        if '|' in activities[i]:
            c += 1
            if i == 0:
                i = 1
            pos.append(i)
    if c != 0:
        for i in pos:
            lis_chain[i] = '|' + lis_chain[i]
        chain = '>'.join(lis_chain)
        return chain
    else:
        return chain


def in_seconds(time: str):
    """
    this function changes the time HH:MM to seconds
    @param time: time in HH:MM in string format
    @return: time in seconds
    """
    return str(int(time.split(':')[0]) * 3600 + int(time.split(':')[-1]) * 60)


def _generate_time():
    """
    this function gets the survey data (cleaned) from the prepare_emd.py and generates the time_of_day dataset.
    The dataset not only contain the information from daily_activity_pattern dataframe but also the information on
    departure and arrival time, trip duration and activity duration all in a sequential chain format.
    @return: returns all of the four datasets as a dataframes which comprises of all chains, activity chains, tour chains,
    and trip chains respectively
    """
    hh_persons, time_df = _prepare_emd()
    # changing the hour and minutes to seconds for convenience
    # Hour:7	Minute: 45 -> 27900s
    time_df.insert(9, 'departure_time',
                   time_df['departure_hour'].astype(int) * 3600 + time_df['departure_minute'].astype(int) * 60)
    time_df['departure_time_chain'] = time_df['departure_hour'] + ':' + time_df['departure_minute']
    time_df.insert(14, 'arrival_time',
                   time_df['arrival_hour'].astype(int) * 3600 + time_df['arrival_minute'].astype(int) * 60)
    time_df['arrival_time_chain'] = time_df['arrival_hour'] + ':' + time_df['arrival_minute']
    print('Time converted to seconds')
    # Type casting to string for easier grouping
    time_df = time_df.applymap(str)
    time_df.to_csv(config['TOD']['ungrouped'])
    time_df = time_df.groupby([*grouping_pid, *personal_attributes])[
        ['departure_time', 'arrival_time', 'departure_time_chain', 'arrival_time_chain']].agg('>'.join)
    # adding socio-economic attributes along with the chains
    time_df = pd.merge(time_df, activity_df, on=[*grouping_pid, *personal_attributes], how='left')
    time_df['time_chain'] = time_df.apply(lambda row: '>'.join(
        alternate_list(row['departure_time_chain'].split('>'), row['arrival_time_chain'].split('>'))), axis=1)
    # getting the first activity from the list of activities
    time_df['first_activity'] = time_df['activity_chain'].str.split('>').str[0]
    # removing activities that don't start from home
    time_df = time_df[time_df['first_activity'].isin(home_activity)]
    # getting the last activity from the list of activities
    time_df['last_activity'] = time_df['activity_chain'].str.split('>').str[-1]
    # removing activities that don't end at home
    time_df = time_df[time_df['last_activity'].isin(home_activity)]
    # dropping columns for easier understanding
    time_df.drop(time_df.filter(regex='(nb|first|last|primary|actual)').columns, axis=1, inplace=True)

    '''
    ACTIVITY_CHAIN with time chains
    '''
    activity_time_df = time_df.copy()
    activity_time_df = activity_time_df.rename(
        columns={'time_chain': 'activity_time_chain'})
    find_duration(activity_time_df)
    activity_time_df.drop(activity_time_df.filter(regex='(departure|arrival)').columns, axis=1, inplace=True)
    activity_time_df.to_csv(config['TOD']['datasets'] + 'activity_non_condensed_time_df.csv', index=False)

    '''
    TOUR_CHAIN with time chains
    '''
    time_df.drop(time_df.filter(regex='trip').columns, axis=1, inplace=True)
    time_df['tour_chain'] = time_df['activity_chain'].astype(str).apply(make_tour)
    time_df['tour_rank'] = time_df['tour_chain'].apply(
        lambda row: '|'.join([str(i) for i in get_position_list(row.split('|'))]))
    time_df['tour_time_chain'] = time_df.astype(str).apply(
        lambda row: make_chain_on_reference(row['tour_chain'], row['time_chain']), axis=1)
    tour_time_df = time_df.astype(str).apply(lambda row: row.str.split('|').explode()).reset_index(drop=True)
    tour_time_df['tour_time_chain'] = tour_time_df['tour_time_chain'].apply(
        lambda row: row[:-1] if row[-1] == '>' else row)
    tour_time_df['tour_chain_rank'] = tour_time_df['tour_chain'] + tour_time_df['tour_rank']
    # tour_time_df = time_df.assign(
    #     tour_time_chain = time_df.tour_time_chain.str.split('|')).explode('tour_time_chain').reset_index(drop = True)
    tour_time_df = tour_time_df.drop(columns=['time_chain', 'activity_chain'])
    tour_time_df['departure_time_chain'] = tour_time_df['tour_time_chain'].apply(
        lambda row: '>'.join([i.split('-')[0] for i in row.split('>')]))
    tour_time_df['arrival_time_chain'] = tour_time_df['tour_time_chain'].apply(
        lambda row: '>'.join([i.split('-')[-1] for i in row.split('>')]))
    tour_time_df['departure_time'] = tour_time_df['tour_time_chain'].apply(
        lambda row: '>'.join([in_seconds(i.split('-')[0]) for i in row.split('>')]))
    tour_time_df['arrival_time'] = tour_time_df['tour_time_chain'].apply(
        lambda row: '>'.join([in_seconds(i.split('-')[-1]) for i in row.split('>')]))
    find_duration(tour_time_df)
    tour_time_df.drop(tour_time_df.filter(regex='(departure|arrival)').columns, axis=1, inplace=True)
    tour_time_df.to_csv(config['TOD']['datasets'] + 'tour_non_condensed_time_df.csv', index=False)

    '''
    TRIP_CHAIN with time chains`    
    '''
    time_df.drop(time_df.filter(regex='tour').columns, axis=1, inplace=True)
    time_df['trip_chain'] = time_df['activity_chain'].apply(make_trip)
    time_df['trip_time_chain'] = time_df.apply(
        lambda row: make_chain_on_reference(row['trip_chain'], row['time_chain']), axis=1)
    trip_time_df = time_df.astype(str).apply(lambda row: row.str.split('|').explode()).reset_index(drop=True)
    trip_time_df['trip_time_chain'] = trip_time_df['trip_time_chain'].apply(
        lambda row: row[:-1] if row[-1] == '>' else row)
    # trip_time_df = time_df.assign(
    #     trip_time_chain = time_df.trip_time_chain.str.split('|')).explode('trip_time_chain').reset_index(drop = True)
    trip_time_df = trip_time_df.drop(columns=['time_chain'])
    trip_time_df['departure_time_chain'] = trip_time_df['trip_time_chain'].apply(
        lambda row: '>'.join([i.split('-')[0] for i in row.split('>')]))
    trip_time_df['arrival_time_chain'] = trip_time_df['trip_time_chain'].apply(
        lambda row: '>'.join([i.split('-')[-1] for i in row.split('>')]))
    trip_time_df['departure_time'] = trip_time_df['trip_time_chain'].apply(
        lambda row: '>'.join([in_seconds(i.split('-')[0]) for i in row.split('>')]))
    trip_time_df['arrival_time'] = trip_time_df['trip_time_chain'].apply(
        lambda row: '>'.join([in_seconds(i.split('-')[-1]) for i in row.split('>')]))
    find_duration(trip_time_df)
    trip_time_df.drop(time_df.filter(regex='(departure|arrival|activity)').columns, axis=1, inplace=True)
    trip_time_df.to_csv(config['TOD']['datasets'] + 'trip_non_condensed_time_df.csv', index=False)
    print('-----all time-of-day datasets were successfully generated-----')
    # A complete dataset with all the data in csv format
    # adding all the information in the general file
    time_df = time_df.rename(
        columns={'time_chain': 'activity_time_chain'})
    time_df['tour_chain'] = time_df['activity_chain'].astype(str).apply(make_tour)
    time_df['tour_time_chain'] = time_df.astype(str).apply(
        lambda row: make_chain_on_reference(row['tour_chain'], row['activity_time_chain']), axis=1)
    time_df.to_csv(config['TOD']['time_of_day'], index=False)

    return time_df, activity_time_df, tour_time_df, trip_time_df

def find_duration(df: pd.DataFrame):
    """
    the function finds the trip duration and activity duration from the dataframe taken as an input.
    @param df: the dataframe whose duration columns are to be added
    @return: the modified dataframe
    """
    # making a dataframe of arrival and departure time for subtraction calculation
    arrival_time = pd.DataFrame(_split_convert(df.arrival_time, '>'))
    departure_time = pd.DataFrame(_split_convert(df.departure_time, '>'))
    # arrival_time.to_csv(config['TOD']['arrival_time'])
    # departure_time.to_csv(config['TOD']['departure_time'])
    '''
    Trip Duration of all trips were calculated by 
    = arrival_time - departure_time 
    Example: Home>Work>Home departure_time = 14400>46800 arrival_time = 16200>48600
    trip_duration = 1800.0 for Home>Work trip & 1800.0 for Work>Home trip
    '''
    # getting travel times of reaching next activity
    trip_duration = arrival_time.subtract(departure_time)
    # Changing the NaN values to '' so that it can be concatenated into a string
    trip_duration = trip_duration.applymap(str)
    # concatenating the travel times of consecutive activities and storing it in trip_duration
    trip_duration['trip_duration'] = pd.Series(trip_duration.fillna('').values.tolist()).str.join('|').apply(
        lambda row: clean_chain(row, '|'))
    # trip_duration.to_csv(config['TOD']['trip_duration'])
    df['trip_duration'] = trip_duration['trip_duration'].values
    # segregates trip duration from chain into different trip columns
    # time_df = chain_dict_segregation(time_df, 'trip_chain_chain', 'trip_duration', '|')
    print('Trip Duration of each trip was computed')
    '''
    Activity Duration of all the activities except first and last (Home) was calculated by:
    = next departure_time - previous arrival_time  
    Example: Home>Work>Home departure_time = 14400>46800 arrival_time = 16200>48600
    activity_duration = 30600.0 for Work activity
    '''
    # getting activity durations of each activity
    departure_time = np.array(departure_time)
    departure_time = [[j for j in i if not math.isnan(j)] for i in departure_time]
    remove_first(departure_time)
    departure_time = pd.DataFrame(departure_time)
    arrival_time = np.array(arrival_time)
    arrival_time = [[j for j in i if not math.isnan(j)] for i in arrival_time]
    remove_last(arrival_time)
    arrival_time = pd.DataFrame(arrival_time)
    activity_duration = departure_time.subtract(arrival_time)
    # Changing the NaN values to '' so that it can be concatenated into a string
    activity_duration = activity_duration.applymap(str)
    # concatenating the durations of all activities and storing it in activity_duration
    activity_duration['activity_duration'] = pd.Series(
        activity_duration.fillna('').values.tolist()).str.join('|').apply(lambda row: clean_chain(row, '|'))
    # activity_duration.to_csv(config['TOD']['activity_duration'])
    df['activity_duration'] = activity_duration['activity_duration'].values
    # segregates activity duration from chain into different activity columns
    # time_df = chain_dict_segregation(time_df, 'intermediate_activity', 'activity_duration', '|')
    print('Activity Duration of each activity was computed')
    # time_df.to_csv(config['TOD']['datasets'] + 'activity_non_condensed_time_df.csv', index = False)


if __name__ == '__main__':
    _generate_time()