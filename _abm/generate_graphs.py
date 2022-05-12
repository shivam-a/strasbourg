import configparser

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set()
from prepare_emd import grouping_pid
# change the root directory to where CONFIG is kept
config = configparser.ConfigParser()
config.read(r'CONFIG.txt')

def _generate_bar_chart(file_name: str):
    """
    generates bar charts as png images based on the frequency table of independent variables
    @param file_name: the file name of the dataset

    """
    df_sheets = pd.read_excel(
        config['ANALYSIS']['frequency'] + file_name + '_frequency.xlsx',
        sheet_name=None, index_col=0)
    for name, sheet in df_sheets.items():
        if name not in grouping_pid:
            plt.figure(figsize=(40, 20))
            plt.title(name + ' Bar Chart')
            plt.xlabel(name, fontdict={'fontsize': 10})
            plt.xticks(rotation=90)
            plt.ylabel('frequency', fontdict={'fontsize': 10})
            plt.bar(sheet[name].head(10), sheet['frequency'].head(10), align='center')
            plt.savefig(
                config['GRAPHS']['frequency'] + file_name + '_' + name + '_bar_chart')
            plt.close('all')
        if 'chain' in name:
            plt.figure(figsize=(90, 60))
            plt.title(name + ' Bar Chart')
            plt.xlabel(name, fontdict={'fontsize': 10})
            plt.xticks(rotation=90)
            plt.ylabel('frequency', fontdict={'fontsize': 10})
            plt.bar(sheet[name].head(50), sheet['frequency'].head(50), align='center')
            plt.savefig(
                config['GRAPHS']['frequency'] + file_name + '_' + name + '_bar_chart')
            plt.close('all')

def _generate_stacked_chart(file_name: str):
    """
    generates the stacked charts  as png images based on contingency table of independent variables
    @param file_name: the file name of the dataset
    """
    df_sheets = pd.read_excel(
        config['ANALYSIS']['contingency'] + file_name + '_contingency.xlsx',
        sheet_name=None, index_col=0)
    for name, sheet in df_sheets.items():
        df = pd.read_excel(
            config['ANALYSIS']['contingency'] + file_name + '_contingency.xlsx',
            sheet_name=name,
            index_col=0)
        df.plot(kind='bar', stacked=True)
        plt.xlabel(list(df.index.values))
        plt.savefig(
            config['GRAPHS']['contingency'] + file_name + '_' + name + '_stacked_chart')
        plt.close('all')

def time_data_graph(df: pd.DataFrame, file_name: str):
    """
    generates count vs time graph for each trip based the dataframe
    @param df: the dataframe that has trips as index and different time as columns
    @param file_name: the file name of the dataset
    @return:
    """
    df.reset_index(level=df.index.names, inplace=True)
    df = df.dropna()
    for index, row in df.iterrows():
        trip = row['trip']
        data = df.set_index('trip').loc[[trip]].melt(var_name='datetime')
        data['hour'] = data['datetime'].str.split(':').str[0].astype(int).apply(
            lambda r: r - 24 if r >= 24 else r).astype(str)
        data['minute'] = data['datetime'].str.split(':').str[-1].astype(int).map("{:02}".format).astype(str)
        data['datetime'] = data['hour'] + ':' + data['minute']
        data.sort_values(by=['datetime'], inplace=True)
        data.drop(columns=['hour', 'minute'], inplace=True)
        data = data[data['value'] != 0]
        data.plot(kind='scatter', x='datetime', y='value', color='r')
        plt.xticks(rotation=90)
        plt.savefig(
            config['GRAPHS']['tod_analysis'] + '_'.join(trip.split('>')) + '_' + file_name + '_time_graph')
        plt.close('all')

def distance_data_graph(df: pd.DataFrame, file_name: str):
    """
    generates count vs distance graph for each trip based the dataframe
    @param df: the dataframe that has trips as index and different distances as columns
    @param file_name: the file name of the dataset
    """
    df.reset_index(level=df.index.names, inplace=True)
    df = df.dropna()
    for index, row in df.iterrows():
        trip = row['trip']
        data = df.set_index('trip').loc[[trip]].melt(var_name='distance')
        data.sort_values(by=['distance'], inplace=True)
        data = data[data['value'] != 0]
        data.plot(kind='scatter', x='distance', y='value', color='r')
        plt.xticks(rotation=90)
        plt.savefig(
            config['GRAPHS']['loa_analysis'] + '_'.join(trip.split('>')) + '_' + file_name + '_distance_graph')
        plt.close('all')

