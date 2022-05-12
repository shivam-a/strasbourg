from copy import deepcopy
from itertools import combinations
from scipy.stats import chi2_contingency
from statsmodels.stats.outliers_influence import variance_inflation_factor
from time_of_day import _generate_time
from daily_activity_pattern import _generate_chain
from location_of_activity import _generate_location
from regression_analysis import _regression_analysis
from generate_graphs import _generate_bar_chart, _generate_stacked_chart
from generate_graphs import *
from location_of_activity import *

config = configparser.ConfigParser()
# change the root directory to where CONFIG is kept
os.chdir(os.path.dirname(sys.path[0]))
config.read(r'CONFIG.txt')

chain_df, activity_nc_chain_df, tour_nc_chain_df, trip_nc_chain_df = _generate_chain()
time_df, activity_nc_time_df, tour_nc_time_df, trip_nc_time_df = _generate_time()
location_df, activity_nc_location_df, tour_nc_location_df, trip_nc_location_df = _generate_location()

def generate_condense_df(df: pd.DataFrame, chain: str):
    """
    this function aggregates/condenses the dataframes from daily_activity_pattern.py based on the frequency (30)
    and percentage (1 %) of occurrences of factors in dependent and independent variable respectively. Generates
    the condensed datasets (csv).
    @param df: dataframe that needs to condensed
    @param chain: specific chain
    @return condensed dataframe
    """
    def condense_category(col, min_freq=0.01, new_name='other'):
        series = pd.value_counts(col)
        mask = (series/series.sum()).lt(min_freq)
        if chain in col.name:
            mask = series.lt(30)
        if chain not in col.name:
            mask = series.lt(0)
        return pd.Series(np.where(col.isin(series[mask].index), new_name, col))
    print('-----datasets were condensed successfully-----')
    return df.apply(condense_category, axis=0)

activity_c_chain_df = generate_condense_df(activity_nc_chain_df, 'activity_chain')
activity_c_chain_df.to_csv(config['DAP']['datasets'] + 'activity_condensed_chain_df.csv', index=False)
tour_c_chain_df = generate_condense_df(tour_nc_chain_df, 'tour_chain')
tour_c_chain_df.to_csv(config['DAP']['datasets'] + 'tour_condensed_chain_df.csv', index=False)
trip_c_chain_df = generate_condense_df(trip_nc_chain_df, 'trip_chain')
trip_c_chain_df.to_csv(config['DAP']['datasets'] + 'trip_condensed_chain_df.csv', index=False)
activity_c_time_df = generate_condense_df(activity_nc_time_df, 'activity_chain')
activity_c_time_df.to_csv(config['TOD']['datasets'] + 'activity_condensed_time_df.csv', index=False)
tour_c_time_df = generate_condense_df(tour_nc_time_df, 'tour_chain')
tour_c_time_df.to_csv(config['TOD']['datasets'] + 'tour_condensed_time_df.csv', index=False)
trip_c_time_df = generate_condense_df(trip_nc_time_df, 'trip_chain')
trip_c_time_df.to_csv(config['TOD']['datasets'] + 'trip_condensed_time_df.csv', index=False)
activity_c_location_df = generate_condense_df(activity_nc_location_df, 'activity_chain')
activity_c_location_df = activity_c_location_df[activity_c_location_df['activity_chain'] != 'other']
activity_c_location_df = dataset_activity_wise(activity_c_location_df, 'activity', 'activity_condensed_location')
activity_c_location_df.to_csv(config['LOA']['datasets'] + 'activity_condensed_location_df.csv', index=False)
tour_c_location_df = generate_condense_df(tour_nc_location_df, 'tour_chain')
tour_c_location_df = tour_c_location_df[tour_c_location_df['tour_chain'] != 'other']
tour_c_location_df = dataset_activity_wise(tour_c_location_df, 'tour', 'tour_condensed_location')
tour_c_location_df.to_csv(config['LOA']['datasets'] + 'tour_condensed_location_df.csv', index=False)
trip_c_location_df = generate_condense_df(trip_nc_location_df, 'trip_chain')
trip_c_location_df.to_csv(config['LOA']['datasets'] + 'trip_condensed_location_df.csv', index=False)

def _data_analysis():
    # chain_type = ['activity', 'tour', 'trip']
    # density_type = ['condensed', 'non_condensed']
    # nest = ['chain', 'time', 'location']
    # bar_chart_frequency_table_all()
    # stacked_chart_contingency_table_all()
    # find_multicollinearity_all()
    # check_chi_square_test_all()
    # _biogeme_logit_tour_rank()
    _regression_analysis_all()
    # time_data_analysis(time_df)
    # distance_data_analysis(location_df)

def bar_chart_frequency_table_all():
    bar_chart_frequency_table(activity_nc_chain_df, 'activity_non_condensed_chain')
    bar_chart_frequency_table(activity_c_chain_df, 'activity_condensed_chain')
    bar_chart_frequency_table(tour_nc_chain_df, 'tour_non_condensed_chain')
    bar_chart_frequency_table(tour_c_chain_df, 'tour_condensed_chain')
    bar_chart_frequency_table(trip_nc_chain_df, 'trip_non_condensed_chain')
    bar_chart_frequency_table(trip_c_chain_df, 'trip_condensed_chain')

def bar_chart_frequency_table(df: pd.DataFrame, file_name: str):
    # shortening activities Home -> Ho, Work -> Wo
    # df[chain + '_chain'] = df[chain + '_chain'].apply(lambda row: shorten_name(str(row), '>', 2))
    writer = pd.ExcelWriter(
        config['ANALYSIS']['frequency'] + file_name + '_frequency.xlsx',
        engine='xlsxwriter')
    def get_frequency(dataframe, column_name):
        return dataframe.groupby(column_name).size().reset_index(name='frequency')
        #.sort_values(by = 'frequency', ascending = False)
    def get_percentage(dataframe):
        dataframe['percentage'] = dataframe['frequency'].apply(lambda row: 100 * row / sum(dataframe['frequency']))
        return dataframe
    for column in df:
        if column not in grouping_pid:
            frequency_percentage = get_percentage(get_frequency(df, [column]))
            frequency_percentage.to_excel(writer, sheet_name=column)
    writer.save()
    _generate_bar_chart(file_name)

def stacked_chart_contingency_table_all():
    stacked_chart_contingency_table(activity_nc_chain_df, 'activity_non_condensed_chain')
    stacked_chart_contingency_table(activity_c_chain_df, 'activity_condensed_chain')
    stacked_chart_contingency_table(tour_nc_chain_df, 'tour_non_condensed_chain')
    stacked_chart_contingency_table(tour_c_chain_df, 'tour_condensed_chain')
    stacked_chart_contingency_table(trip_nc_chain_df, 'trip_non_condensed_chain')
    stacked_chart_contingency_table(trip_c_chain_df, 'trip_condensed_chain')

def stacked_chart_contingency_table(df: pd.DataFrame, file_name: str):
    column_comb = [','.join(map(str, comb)) for comb in combinations(socio_economic_attributes, 2)]
    writer = pd.ExcelWriter(
        config['ANALYSIS']['contingency'] + file_name + '_contingency.xlsx',
        engine = 'xlsxwriter')
    def get_contingency(dataframe, column_1, column_2):
        return dataframe.pivot_table(index = column_1, columns = column_2, aggfunc ='size')
    for comb in column_comb:
        # each combination of any two socio economic attribute
        contingency = get_contingency(df, comb.split(',')[0], comb.split(',')[1])
        contingency.to_excel(writer, sheet_name = shorten_name(str(comb), ',', 4))
    writer.save()
    _generate_stacked_chart(file_name)

def check_chi_square_test_all():
    check_chi_square_test('activity_non_condensed_chain')
    check_chi_square_test('activity_condensed_chain')
    check_chi_square_test('tour_non_condensed_chain')
    check_chi_square_test('tour_condensed_chain')
    check_chi_square_test('trip_non_condensed_chain')
    check_chi_square_test('trip_condensed_chain')

def check_chi_square_test(file_name: str):
    df_sheets = pd.read_excel(
        config['ANALYSIS']['contingency'] + file_name + '_contingency.xlsx',
        sheet_name = None, index_col = 0)
    for name, sheet in df_sheets.items():
        df = pd.read_excel(
            config['ANALYSIS']['contingency'] + file_name + '_contingency.xlsx',
            sheet_name = name,
            index_col = 0).replace(np.nan, 0)
        stat, p, dof, expected = chi2_contingency(df.values)
        alpha = 0.05
        print('-----CHI SQUARE TEST-----')
        print(df)
        print(name)
        print('p value is: ' + str(p))
        if p <= alpha:
            print('Dependent (reject H0)')
        else:
            print('Independent (fail to reject H0)')

def find_multicollinearity_all():
    find_multicollinearity('activity_non_condensed_chain')
    find_multicollinearity('activity_condensed_chain')
    find_multicollinearity('tour_non_condensed_chain')
    find_multicollinearity('tour_condensed_chain')
    find_multicollinearity('trip_non_condensed_chain')
    find_multicollinearity('trip_condensed_chain')

def find_multicollinearity(file_name: str):
    df = pd.read_csv(
        config['ANALYSIS']['dummy'] + file_name + '_dummy_df.csv').filter(
        regex='|'.join(socio_economic_attributes))
    vif = pd.DataFrame()
    vif["variables"] = df.iloc[:,:-1].columns
    vif["VIF"] = [variance_inflation_factor(df.iloc[:,:-1].values, i) for i in range(df.iloc[:,:-1].shape[1])]
    vif.to_csv(
        config['ANALYSIS']['multicollinearity'] + file_name + '_multicollinearity.csv')

#
# def get_unique_persons(chain, density):
#     df = pd.read_csv(config['DAP']['datasets'] + chain + '_' + density + '_chain_df.csv', index_col = 0)
#     df.drop_duplicates(subset = socio_economic_attributes)

def time_data_analysis(df: pd.DataFrame):
    df['departure_time_chain'] = df['departure_time_chain'].apply(
        lambda row: '|'.join(row.split('>')))
    df['arrival_time_chain'] = df['arrival_time_chain'].apply(
        lambda row: '|'.join(row.split('>')))
    df, departure_values = chain_dict_segregation(df, 'departure_time_chain', 'trip_chain', '|')
    df, arrival_values = chain_dict_segregation(df, 'arrival_time_chain', 'trip_chain', '|')
    def trip_count(dataframe):
        trip_count_list = []
        trip_count_dict = {}
        def reset_trip_count_dict():
            for trip in trip_nc_chain_df['trip_chain'].unique():
                trip_count_dict[trip] = 0
        for column_name, contents in dataframe.items():
            reset_trip_count_dict()
            for i in contents:
                if i != '':
                    trip_count_dict[i] += 1
            trip_count_list.append(deepcopy(trip_count_dict))
        new_df = pd.DataFrame(trip_count_list).T
        new_df.columns = dataframe.columns
        new_df.sort_index(axis = 1, inplace = True)
        new_df.sort_index(axis = 0, inplace = True)
        new_df.index.name = 'trip'
        return new_df
    trip_count(departure_values).to_csv(config['ANALYSIS']['tod_analysis'] + 'departure_trip_count.csv')
    trip_count(arrival_values).to_csv(config['ANALYSIS']['tod_analysis'] + 'arrival_trip_count.csv')
    time_data_graph(trip_count(departure_values), 'departure')
    time_data_graph(trip_count(arrival_values), 'arrival')

def distance_data_analysis(df: pd.DataFrame):
    df, distance_values = chain_dict_segregation(df, 'distance_chain', 'trip_chain', '|')
    def trip_count(dataframe):
        trip_count_list = []
        trip_count_dict = {}
        def reset_trip_count_dict():
            for trip in trip_nc_location_df['trip_chain'].unique():
                trip_count_dict[trip] = 0
        for column_name, contents in dataframe.items():
            reset_trip_count_dict()
            contents = contents.to_frame().apply(lambda row: row.str.split(',').explode())
            for i, r in contents.iterrows():
                if r.values != ['']:
                    trip_count_dict[r.values[0].strip()] += 1
            trip_count_list.append(deepcopy(trip_count_dict))
        new_df = pd.DataFrame(trip_count_list).T
        new_df.columns = dataframe.columns
        new_df.sort_index(axis = 1, inplace = True)
        new_df.sort_index(axis = 0, inplace = True)
        new_df.index.name = 'trip'
        return new_df
    trip_count(distance_values).to_csv(config['ANALYSIS']['loa_analysis'] + 'distance_trip_count.csv')
    distance_data_graph(trip_count(distance_values), 'distance')

def _regression_analysis_all():
    ####################################### CHAIN DATASETS #######################################
    # _regression_analysis(tour_nc_chain_df, 'tour_chain', socio_economic_attributes,
    #                      2, 'tour_non_condensed_chain', '')
    # _regression_analysis(tour_c_chain_df, 'tour_chain', socio_economic_attributes,
    #                      2,'tour_condensed_chain', '')
    # _regression_analysis(tour_nc_chain_df, 'tour_chain_rank', socio_economic_attributes,
    #                      2,'tour_non_condensed_rank', '')
    # _regression_analysis(tour_c_chain_df, 'tour_chain_rank', socio_economic_attributes,
    #                      2,'tour_condensed_rank', '')

    ###### TOUR CHAIN RANKED 1 ######
    # non_condensed form
    # tour1_nc_rank_df = tour_nc_chain_df[tour_nc_chain_df['tour_chain_rank'].str.contains('1')]
    # _regression_analysis(tour1_nc_rank_df, 'tour_chain_rank', socio_economic_attributes, 2,'tour1_non_condensed_rank', '')
    # condensed form
    # tour1_c_rank_df = generate_condense_df(tour_nc_chain_df[tour_nc_chain_df['tour_chain_rank'].str.contains('1')])
    # _regression_analysis(tour1_c_rank_df, 'tour_chain_rank', socio_economic_attributes, 2,'tour1_condensed_rank', '')

    ###### TOUR CHAIN RANKED 2 ######
    # non_condensed form
    # tour1_independent_variables = tour_nc_chain_df[
    #     tour_nc_chain_df['tour_chain_rank'].str.contains('1')]['tour_chain_rank'].unique()
    # tour2_nc_rank_df = tour_nc_chain_df[
    #     (tour_nc_chain_df['tour_chain_rank'].str.contains('1')) | (tour_nc_chain_df['tour_chain_rank'].str.contains('2'))]
    # _regression_analysis(tour2_nc_rank_df, 'tour_chain_rank',
    #     [*tour1_independent_variables, *socio_economic_attributes], 1, 'tour2_non_condensed_rank', '2')

    ###### TOUR CHAIN RANKED 3 ######
    # tour2_independent_variables = tour_nc_chain_df[
    #     tour_nc_chain_df['tour_chain_rank'].str.contains('2')]['tour_chain_rank'].unique()
    # tour3_nc_rank_df = tour_nc_chain_df[
    #     (tour_nc_chain_df['tour_chain_rank'].str.contains('1')) | (
    #     tour_nc_chain_df['tour_chain_rank'].str.contains('2')) | (
    #     tour_nc_chain_df['tour_chain_rank'].str.contains('3'))]
    # _regression_analysis(tour3_nc_rank_df, 'tour_chain_rank',
    #     [*tour1_independent_variables, *tour2_independent_variables, *socio_economic_attributes], 1,
    #     'tour3_non_condensed_rank', '3')
    ####################################### LOCATION DATASETS #######################################
    location_independent_variables = ['random_distance_zone', 'previous_work',
                                      'previous_school', 'previous_university', 'previous_shopping',
                                      'previous_leisure', 'previous_accompany', 'previous_other', 'previous_home',
                                      'previous_home_getaway', 'size']
    # With all variables
    tour_nc_location_work = pd.read_csv(
        config['LOA']['datasets'] + '/' + 'Work' + '/' + 'tour_non_condensed_location' + '_' + 'Work.csv')
    _regression_analysis(tour_nc_location_work, 'current_iris',
                         [*socio_economic_attributes, *location_independent_variables],
                         2, 'tour_non_condensed_location_work1', '')
    tour_nc_location_work = pd.read_csv(
        config['LOA']['datasets'] + '/' + 'Work' + '/' + 'tour_condensed_location' + '_' + 'Work.csv')
    _regression_analysis(tour_nc_location_work, 'current_iris',
                         [*socio_economic_attributes, *location_independent_variables],
                         2, 'tour_condensed_location_work1', '')
    # # With only location variables
    tour_nc_location_work = pd.read_csv(
        config['LOA']['datasets'] + '/' + 'Work' + '/' + 'tour_non_condensed_location' + '_' + 'Work.csv')
    _regression_analysis(tour_nc_location_work, 'current_iris',
                         location_independent_variables,
                         4, 'tour_non_condensed_location_work2', '')
    tour_nc_location_work = pd.read_csv(
        config['LOA']['datasets'] + '/' + 'Work' + '/' + 'tour_condensed_location' + '_' + 'Work.csv')
    _regression_analysis(tour_nc_location_work, 'current_iris',
                         location_independent_variables,
                         4, 'tour_condensed_location_work2 ', '')
    # # With selected socio-economic and location variables
    tour_nc_location_work = pd.read_csv(
        config['LOA']['datasets'] + '/' + 'Work' + '/' + 'tour_non_condensed_location' + '_' + 'Work.csv')
    _regression_analysis(tour_nc_location_work, 'current_iris',
                         ['age', 'license', 'hh_income', *location_independent_variables],
                         3, 'tour_non_condensed_location_work3', '')
    tour_nc_location_work = pd.read_csv(
        config['LOA']['datasets'] + '/' + 'Work' + '/' + 'tour_condensed_location' + '_' + 'Work.csv')
    _regression_analysis(tour_nc_location_work, 'current_iris',
                         ['age', 'license', 'hh_income', *location_independent_variables],
                         3, 'tour_condensed_location_work3', '')
    # tour_nc_location_school = pd.read_csv(
    #     config['LOA']['datasets'] + '/' + 'School' + '/' + 'tour_non_condensed_location' + '_' + 'School.csv')
    # _regression_analysis(tour_nc_location_school, 'current_iris',
    #                      location_independent_variables,
    #                      4, 'tour_non_condensed_location_school', '')
    # tour_nc_location_school = pd.read_csv(
    #     config['LOA']['datasets'] + '/' + 'School' + '/' + 'tour_non_condensed_location' + '_' + 'School.csv')
    # _regression_analysis(tour_nc_location_school, 'current_iris',
    #                      [*socio_economic_attributes, *location_independent_variables],
    #                      2, 'tour_non_condensed_location_school', '')
    # tour_nc_location_university = pd.read_csv(
    #     config['LOA']['datasets'] + '/' + 'University' + '/' + 'tour_non_condensed_location' + '_' + 'University.csv')
    # _regression_analysis(tour_nc_location_university, 'current_iris',
    #                      [*socio_economic_attributes, *location_independent_variables],
    #                      2, 'tour_non_condensed_location_university', '')
    # tour_nc_location_shopping = pd.read_csv(
    #     config['LOA']['datasets'] + '/' + 'Shopping' + '/' + 'tour_non_condensed_location' + '_' + 'Shopping.csv')
    # _regression_analysis(tour_nc_location_shopping, 'current_iris',
    #                      [*socio_economic_attributes, *location_independent_variables],
    #                      2, 'tour_non_condensed_location_shopping', '')
    # tour_nc_location_leisure = pd.read_csv(
    #     config['LOA']['datasets'] + '/' + 'Leisure' + '/' + 'tour_non_condensed_location' + '_' + 'Leisure.csv')
    # _regression_analysis(tour_nc_location_leisure, 'current_iris',
    #                      [*socio_economic_attributes, *location_independent_variables],
    #                      2, 'tour_non_condensed_location_leisure', '')
    # tour_nc_location_home = pd.read_csv(
    #     config['LOA']['datasets'] + '/' + 'Home' + '/' + 'tour_non_condensed_location' + '_' + 'Home.csv')
    # _regression_analysis(tour_nc_location_home, 'current_iris',
    #                      [*socio_economic_attributes, *location_independent_variables],
    #                      2, 'tour_non_condensed_location_home', '')
    # tour_nc_location_home_getaway = pd.read_csv(
    #     config['LOA']['datasets'] + '/' + 'Home_getaway' + '/' + 'tour_non_condensed_location' + '_' + 'Home_getaway.csv')
    # _regression_analysis(tour_nc_location_home_getaway, 'current_iris',
    #                      [*socio_economic_attributes, *location_independent_variables],
    #                      2, 'tour_non_condensed_location_home_getaway', '')


def shorten_name(shortening_string, separator, by):
    shortening_string = separator.join([x[:by] for x in shortening_string.split(separator)])
    return shortening_string

if __name__ == '__main__':
    _data_analysis()

