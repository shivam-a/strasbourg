#!/usr/bin/env python3

"""
The scrip is for:
1. Splitting chain ov activities distributed on EMD and IRIS
2. Creating pivot tables to check the outcomes of distributing activities from EMD to IRIS
e.g. pivot_activity_count_iris.xlsx
pivot_emd_iris_activity.xlsx
3. Checking the results by joining 2 tables and calculating percentage error
"""
import configparser
import math
import os
import sys
import pandas as pd
from sklearn.metrics import mean_absolute_error
import emd_to_iris

##################
# Data input
##################
config = configparser.ConfigParser()
os.chdir(os.path.dirname(sys.path[0]))
config.read(r'CONFIG.txt')

# csv files
#loa_csv =config['LOA']['location_of_activity']

loa_csv = config['LOA']['location_of_activity_iris']
EMD_activities_csv = config['input']['deplacements_emd_activities']

path_out =r'.\output\_results'



def read_loa(loa_csv):
    columns = ['index','hh_id','sector', 'sector_fine', 'sample_id', 'person_id', 'zone_chain', 'activity_chain', 'activity_actual_chain', 'chain_iris']
    loa_df = pd.read_csv(loa_csv, sep=',', skipinitialspace=True, dtype=str, usecols=columns)
    return loa_df

def find_duplciated_home(loa_csv, simple_approach=False):
    '''
     Remove last activity home from a cahin of activities in simple approach
    '''
    df = read_loa(loa_csv)

    # check Start Home != End Home
    df['Start Home != End Home'] = df['activity_actual_chain'].astype(str).apply(
        lambda row: True if row.split('>')[0] != row.split('>')[-1] else False)

    # Simple does not apply anymore
    if simple_approach:
        df['chain_iris_n'] = df.chain_iris.str.split(">").str[:-1]
        df['activity_chain_n'] = df.activity_chain.str.split(">").str[:-1]
        print(df.head(3))
    else:
        # Convert column to a list format
        df['chain_iris_n'] = df['chain_iris'].apply(lambda x: x.replace('>', ','))
        df['chain_iris_n'] = df['chain_iris_n'].apply(lambda x: x.split(','))
        df['activity_chain_n'] = df['activity_chain'].apply(lambda x: x.replace('>', ','))
        df['activity_chain_n'] = df['activity_chain_n'].apply(lambda x: x.split(','))
        df['emd_chain_n'] = df['zone_chain'].apply(lambda x: x.replace('>', ','))
        df['emd_chain_n'] = df['emd_chain_n'].apply(lambda x: x.split(','))

        #print('Strings converted to a list ', df.head(3))

        # Remove duplicated value at the last position from the list in each row: lambda
        cols = ['chain_iris_n', 'activity_chain_n', 'emd_chain_n']
        for col in cols:
            #df[col] = df.apply(lambda row: row[col][:-1] if row[col][0] == row[col][-1] else row[col], axis=1)
            df[col] = df.apply(lambda row: row[col][:-1] if row['Start Home != End Home'] ==False else row[col], axis=1)
        print('Duplicated home removed ', df[['chain_iris_n', 'activity_chain_n', 'emd_chain_n']])

    xls_file = os.path.join(path_out, '{}.{}'.format('location_of_activity_iris_exl_last_home', 'xlsx'))
    df.to_excel(xls_file, sheet_name='loa_iris_excl_last_home')

    return df

def split_activities(df, path_out):
    '''
    Split the chain of activities and zones into rows
    '''
    # Check the number of items in a list in rows
    df['count_emd'] = df.apply(lambda row: len(row['emd_chain_n']), axis=1)
    df['count_activity'] = df.apply(lambda row: len(row['activity_chain_n']), axis=1)
    df['count_iris'] = df.apply(lambda row: len(row['chain_iris_n']), axis=1)
    df['diff_count'] = df.apply(lambda row: row['count_iris']-row['count_activity'], axis=1)
    print('new columns ', df[['count_iris', 'count_iris']])

    #Save df to csv
    #df_a = 'loa_split_count.csv'
    #save_csv(path_out, df, df_a)

    # set the index on all columns that must NOT be exploded first
    df_split = df.set_index([ 'index','hh_id','sector', 'sector_fine', 'sample_id', 'person_id',
                              'activity_chain', 'chain_iris', 'zone_chain', 'Start Home != End Home',
                              'count_activity', 'count_iris', 'diff_count']).apply(lambda x: x.apply(pd.Series).stack()).reset_index()
    # Convert IRIS to str
    df_split['chain_iris_n']= df_split['chain_iris_n'].astype(str)
    df_split['emd_chain_n'] = df_split['emd_chain_n'].astype(str)
    df_split['hh_id'] = df_split['hh_id'].astype(float).astype(int)

    # Save to csv
    df_name = 'loa_split_chain_iris_activity_emd'
    save_csv(path_out, df_split, '{}.{}'.format(df_name, 'csv'))
    xls_file = os.path.join(path_out, '{}.{}'.format(df_name, 'xlsx'))
    df_split.to_excel(xls_file , sheet_name='activity_iris_split',
                                  index=False)

    return df_split

def pivot_table(df):

    print('######### PIVOT tables ##############\n')

    df['chain_iris_n'] = df['chain_iris_n'].astype(str)
    print(df.head())
    print(df.dtypes)

    ##############

    piv_tab5 = pd.pivot_table(data= df,
                              index = ['chain_iris_n'],
                              values =['index'],
                              columns =['activity_chain_n'],
                              aggfunc= 'count',
                             fill_value=0)#.stack()

    piv_tab5.index.name = 'chain_iris_n'
    piv_tab5 = piv_tab5.reset_index()
    print('pivot_activity_count_iris: \n', piv_tab5)

    df_name = 'pivot_activity_count_iris'
    save_csv(path_out, piv_tab5, '{}.{}'.format(df_name, 'csv'))
    xls_file = os.path.join(path_out, '{}.{}'.format(df_name, 'xlsx'))
    piv_tab5.to_excel( xls_file, sheet_name='activity_count_iris')


def save_csv(path_out, df, df_name):

    file = os.path.join(path_out, df_name)
    df.to_csv(file, index=False, sep = ';')

def count_activities_column(in_csv):

    df= pd.read_csv(in_csv, sep=',', skipinitialspace=True, dtype=str)
    count_Accompany= (df.activity_chain.str.count("Accompany").sum())
    count_Other = (df.activity_chain.str.count("Other").sum())
    count_Home = (df.activity_chain.str.count("Home").sum())
    count_Work = (df.activity_chain.str.count("Work").sum())
    Shopping =(df.activity_chain.str.count("Shopping").sum())
    count_Home_getaway = (df.activity_chain.str.count("Home_getaway").sum())
    print(count_Home, count_Home_getaway, count_Work, Shopping, count_Accompany, count_Other)

################################
# Check results of ditribuing activities from EMd to IRIS
#################################
def check_iris_per_emd(csv_loa_iris):
    '''
    1. Make pivot table of all activity types per iris
    2. Merge the df with zone_to_iris_tabulate table (percentage of iris area per emd zone)
    3. Check: Calculate the percentage of activies per emd
    Save to xls
    '''
    ###############################
    # 1 Pivot : aggregated amount of activity-trips by EMD and IRIS
    ##############################
    df = pd.read_csv(csv_loa_iris, sep=';', dtype={ 'chain_iris_n': str, 'emd_chain_n': str })
    print(df.head())
    print(df.columns)
    groupby_tab = df.groupby(['emd_chain_n', 'chain_iris_n']).agg(
        activity_amount =pd.NamedAgg(column="activity_chain_n", aggfunc="count")).reset_index()
    groupby_tab = groupby_tab.rename(columns={'emd_chain_n':'emd_zone','chain_iris_n' : 'iris_zone'})

    # groupby_tab['chain_iris_n'] = groupby_tab['chain_iris_n'].astype(str)
    print('groupby_1: \n ', groupby_tab)
    print(groupby_tab.head())
    ''' Example:
            emd_zone  iris_zone  activity_amount
        0   001002  670860000                1
        1   001003  671300104                6
        2   001004  671300101               26
    '''
    # To csv and excel
    df_name = 'pivot_emd_iris_activity_amount'
    save_csv(path_out, groupby_tab, '{}.{}'.format(df_name, 'csv'))
    xls_file = os.path.join(path_out, '{}.{}'.format(df_name, 'xlsx'))

    groupby_tab.to_excel(xls_file, sheet_name='emd_iris_activity_amount',
                         index=False)

    #################################################
    # Checking the distribution by IRIS zone
    #################################################

    # 2: Merge zone_iris_tabulate with the df
    emd_irirs_tabulate = emd_to_iris.zone_to_iris()
    #print('emd_irirs_tabulate', emd_irirs_tabulate.columns)
    #print('groupby_tab', groupby_tab.columns)

    merge_df = pd.merge(emd_irirs_tabulate, groupby_tab.reset_index(), how='left', left_on=['code_emd', 'CODE_IRIS'],
                      right_on=['emd_zone',  'iris_zone'])
    print(merge_df.head(6))

    # 3 Calculate sum of activities per code_emd
    merge_df = merge_df.merge(merge_df.groupby('code_emd')
             .agg(activities_emd_sum =pd.NamedAgg(column="activity_amount", aggfunc="sum")),
             left_on='code_emd',
                            right_index=True)

    # 4 Merge df with the orginal deplacement activities per emd
    # the number activity is heigher than this taken in loa, in loa activities not starting from home were removed)
    emd_activities = pd.read_csv(EMD_activities_csv, sep=';', dtype={ 'EMD': str})
    merge_df = pd.merge(merge_df, emd_activities.reset_index(), how='left', left_on=['code_emd'],
                      right_on=['EMD'])
    merge_df.rename(columns={ 'no_activities_org': 'org_activities_emd_sum' }, inplace=True)

    # 5 Remove emd zone with no activities
    #merge_df =merge_df[pd.notnull(merge_df['emd_zone'])]
    merge_df = merge_df[merge_df['emd_zone'].notna()]

    #  6.1 Distribute activities to iris based on the orginal PERCENTAGAE
    merge_df['cal_activities_area_perc'] =  merge_df.apply(
        lambda row: math.floor(float(row['activities_emd_sum']) * (float(row['PERCENTAGE'] / 100.00)) + 0.5),axis=1 )

    #  6.2 Distribute orginal activities to iris based on the orginal PERCENTAGAE
    merge_df['cal_org_activities_area_perc'] = merge_df.apply(
        lambda row: math.floor(float(row['org_activities_emd_sum']) * (float(row['PERCENTAGE'] / 100.00)) + 0.5), axis=1)

    # 7 Calculate the percentage of the activity per iris to the sum per emd -> check the percentage of distribution of activities per IRIS
    merge_df['perc_cal_activity'] = ((merge_df['activity_amount'] / merge_df['activities_emd_sum']) * 100).round(decimals=2)

    # 8.1 Percentage Error: Divide by the Exact Value abs(approx value- exact value/ exact value)*100
    # excact value is the activities_emd_sum *PERCENTAGE
    merge_df['Pct_Error_smaple'] = (((merge_df['activity_amount'] - merge_df['cal_activities_area_perc']) /
                                         merge_df['cal_activities_area_perc']) * 100).abs().round(decimals=2)

    # 8.2 Percentage Error: Divide by the Exact Value abs(approx value- exact value/ exact value)*100
    # # excact value is the org_activities_emd_sum *PERCENTAGE
    merge_df['Pct_Error_act_org'] = (((merge_df['activity_amount'] - merge_df['cal_org_activities_area_perc']) /
                                         merge_df['cal_org_activities_area_perc']) * 100).abs().round(decimals=2)

    # mean absolute percentage error
    mape2= mean_absolute_error(merge_df['cal_org_activities_area_perc'], merge_df['activity_amount'], multioutput='raw_values')
    print('Mean absolute percentage error',  mape2)
    # merge_df.drop('index_y')
    #print(merge_df.head(6))

    df_name = 'check_emd_iris_perc_activity'
    xls_file = os.path.join(path_out, '{}.{}'.format(df_name, 'xlsx'))
    merge_df.to_excel(xls_file, sheet_name='emd_iris_perc_activity',
                          index=False)

def refine_loa_file(loa_csv, path_out):

    df = find_duplciated_home(loa_csv, simple_approach=False)
    dfs=split_activities( df, path_out)
    pivot_table(dfs)


if __name__ == '__main__':

    refine_loa_file(loa_csv, path_out)
    #in_csv = loa_csv =config['DAP']['DAP_activity_chain']
    #count_activities_column(in_csv)

    csv_loa_iris = os.path.join(path_out ,'{}.{}'.format('loa_split_chain_iris_activity_emd', 'csv'))
    check_iris_per_emd(csv_loa_iris)