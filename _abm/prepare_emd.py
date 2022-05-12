import os
import sys
import pandas as pd
import configparser
config = configparser.ConfigParser()
# change the root directory to where CONFIG is kept
os.chdir(os.path.dirname(sys.path[0]))
config.read(r'CONFIG.txt')
grouping = ['sector', 'sector_fine', 'sample_id']
grouping_pid = ['sector', 'sector_fine', 'sample_id', 'person_id']
grouping_tid = ['sector', 'sector_fine', 'sample_id', 'trip_id']
grouping_pid_tid = ['sector', 'sector_fine', 'sample_id', 'person_id', 'trip_id']

def _prepare_emd():
    """
    this function cleans the data from the EMD survey by taking the DEPLACEMENTS, PERSONNES, MENAGE, TRAJETS as inputs,
    adds any missing data, renames column and row data for better understanding. The final dataframe comprises of
    columns that describe the individual or household characteristics and rows describe each observation.

    @return: the three merged dataframes (1. persons_households 2. trips_persons_households
    3. trips_routes_persons_households)
    """
    # rename EMD-variables (just to make data more understandable)
    # dictionary for all files
    households_variables = {
        'SECT1': 'sector',
        'SECT2': 'sector_fine',
        'ECH': 'sample_id',
        'L31 ': 'hh_income'
    }
    persons_variables = {
        'SECT1': 'sector',
        'SECT2': 'sector_fine',
        'ECH': 'sample_id',
        'NUMPERS': 'person_id',
        'P2': 'sex',
        'P4': 'age',
        'P8': 'enrollment',
        'P7': 'license',
        'P9': 'occupation',
    }
    trip_variables = {
        'SECT1': 'sector',
        'SECT2': 'sector_fine',
        'ECH': 'sample_id',
        'NUMPERS': 'person_id',
        'NUMDEP': 'trip_id',
        'D2A': 'origin_motive',
        'D3': 'origin_zone',
        'D4A': 'departure_hour',
        'D4B': 'departure_minute',
        'D5A': 'destination_motive',
        'D7': 'destination_zone',
        'D8A': 'arrival_hour',
        'D8B': 'arrival_minute',
    }
    routes_variables = {
        'SECT1': 'sector',
        'SECT2': 'sector_fine',
        'ECH': 'sample_id',
        'NUMPERS': 'person_id',
        'NUMDEP': 'trip_id',
        'T3': 'mode_used',
    }
    opinion_variables = {
        'SECT1': 'sector',
        'SECT2': 'sector_fine',
        'ECH': 'sample_id',
        'NUMPERS': 'person_id',
        'L29': 'mode'
    }
    def rename_motive(cell):
        value = int(cell)
        if value == 1:
            return 'Home'
        elif value == 2:
            return 'Home_getaway'
        elif value < 20:
            return 'Work'
        elif value < 29:
            return 'School'
        elif value < 30:
            return 'University'
        elif value < 40:
            return 'Shopping'
        elif 50 < value < 60:
            return 'Leisure'
        elif value < 70:
            return 'Accompany'
        else:
            return 'Other'

    def rename_age(cell):
        if cell == 'missing':
            return cell
        value = int(cell)
        if value <= 14:
            return '00_14'
        elif value <= 18:
            return '15_18'
        elif value <= 26:
            return '19_26'
        elif value <= 65:
            return '27_65'
        # elif value <= 74:
        #     return '60_74'
        else:
            return '65_'

    def rename_sex(cell):
        if cell == 'missing':
            return cell
        value = int(cell)
        if value == 1:
            return 'M'
        else:
            return 'F'

    def rename_enrollment(cell):
        if cell == 'missing':
            return cell
        value = int(cell)
        if value == 0:
            return 'in_school'
        elif value == 1:
            return 'primary'
        elif value == 2:
            return 'secondary_cap'
        elif value == 3:
            return 'secondary_bep'
        elif value == 4:
            return 'bac_0'
        elif value == 5:
            return 'bac_2'
        elif value == 6:
            return 'bac_3'
        elif value == 7:
            return 'learning'
        else:
            return 'no_studies'

    def rename_license(cell):
        if cell == 'missing':
            return cell
        value = int(cell)
        if value == 1:
            return 'yes'
        elif value == 2:
            return 'no'
        else: return 'accompanied'

    def rename_occupation(cell):
        if cell == 'missing':
            return cell
        value = int(cell)
        if value == 1:
            return 'full_time'
        elif value == 2:
            return 'part_time'
        elif value == 3:
            return 'training'
        elif value == 4:
            return 'student'
        elif value == 5:
            return 'pupil'
        elif value == 6:
            return 'job_seeker'
        elif value == 7:
            return 'retired'
        elif value == 8:
            return 'at_home'
        else:
            return 'other'

    def rename_income(cell):
        if cell == 'missing':
            return cell
        value = int(cell)
        if value == 1:
            return '0_5K'
        elif value == 2:
            return '5K_10K'
        elif value == 3:
            return '10K_15K'
        elif value == 4:
            return '15K_20K'
        elif value == 5:
            return '20K_25K'
        elif value == 6:
            return '25K_30K'
        elif value == 7:
            return '30K_40K'
        elif value == 8:
            return '40K_60K'
        elif value == 9:
            return '60K_100K'
        elif value == 10:
            return '100K_'
        else:
            return 'no_answer'

    def rename_mode_used(cell):
        value = int(cell)
        if value == 11:
            return 'bike'
        elif value == 21 | value == 22:
            return 'car'
        elif value > 30 & value < 62:
            return 'transit'
        else:
            return 'other'

    def rename_mode(cell):
        if cell == 'missing':
            return cell
        value = int(cell)
        if value == 1:
            return 'walking'
        elif value == 2:
            return 'car'
        elif value == 3:
            return 'train'
        elif value == 4:
            return 'bus'
        elif value == 5:
            return 'bike'
        else:
            return 'other'

    # read deplacement.csv (from EMD)
    # only keep the variables of interest and rename them
    trips = pd.read_csv(config['input']['survey'] + 'DEPLACEMENTS.csv', sep=';', dtype=str)
    # split time
    trips['D4A'] = trips.D4.str.extract('(\d\d)\d\d')
    trips['D4B'] = trips.D4.str.extract('\d\d(\d\d)')
    trips['D8A'] = trips.D8.str.extract('(\d\d)\d\d')
    trips['D8B'] = trips.D8.str.extract('\d\d(\d\d)')
    trips = trips[list(trip_variables.keys())]
    # Added the missing destination motive value
    trips = trips.rename(columns=trip_variables)
    trips[['destination_motive']] = trips[['destination_motive']].fillna('61')
    trips['origin_actual_motive'] = trips['origin_motive']
    trips['destination_actual_motive'] = trips['destination_motive']
    # rename origin and destination motives
    trips['origin_motive'] = trips['origin_motive'].apply(rename_motive)
    trips['destination_motive'] = trips['destination_motive'].apply(rename_motive)
    trips = trips.dropna()
    # add the missing destination motive (which is probably Accompany)

    persons = pd.read_csv(config['input']['survey'] + 'PERSONNES.csv', sep=';', dtype=str)
    persons = persons[list(persons_variables.keys())]
    # renaming variables
    persons = persons.rename(columns=persons_variables)
    persons = persons.fillna('missing')
    persons['sex'] = persons['sex'].apply(rename_sex)
    persons['age'] = persons['age'].apply(rename_age)
    persons['enrollment'] = persons['enrollment'].apply(rename_enrollment)
    persons['occupation'] = persons['occupation'].apply(rename_occupation)
    persons['license'] = persons['license'].apply(rename_license)
    persons = persons.dropna()

    households = pd.read_csv(config['input']['survey'] + 'MENAGE.csv', sep=';', dtype=str)
    households = households[list(households_variables.keys())]
    households = households.rename(columns=households_variables)
    households['hh_income'] = households['hh_income'].apply(rename_income)
    households = households.dropna()

    routes = pd.read_csv(config['input']['survey'] + 'TRAJETS.csv', sep=';', dtype=str)
    routes = routes[list(routes_variables.keys())]
    routes = routes.rename(columns=routes_variables)
    routes['mode_used'] = routes['mode_used'].apply(rename_mode_used)
    # routes = routes.dropna()

    opinion = pd.read_csv(config['input']['survey'] + 'OPINION.csv', sep=';', dtype=str)
    opinion = opinion[list(opinion_variables.keys())]
    opinion = opinion.rename(columns=opinion_variables)
    opinion = opinion.fillna('missing')
    opinion['mode'] = opinion['mode'].apply(rename_mode)
    # opinion = opinion.dropna()

    persons_households = pd.merge(
        persons, households, on=grouping, how='left')
    trips_routes = pd.merge(
        trips, routes, on=grouping_pid_tid, how='left').drop_duplicates()
    trips_persons_households = pd.merge(
        trips, persons_households, on=grouping_pid, how='left').drop_duplicates()
    trips_routes_persons_households = pd.merge(
        trips_routes, persons_households, on=grouping_pid, how='left').drop_duplicates(subset=[*grouping_pid,
                                                                                               'origin_motive',
                                                                                               'origin_zone',
                                                                                               'departure_hour',
                                                                                               'departure_minute',
                                                                                               'destination_motive',
                                                                                               'destination_zone',
                                                                                               'arrival_hour',
                                                                                               'arrival_minute'])
    return persons_households, trips_persons_households

# remove list of items from a list
def remove_multiple(lis, rem):
    return [item for item in lis if item not in rem]

if __name__ == '__main__':
    _prepare_emd()
