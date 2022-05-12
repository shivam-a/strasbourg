'''
author: sliz
data: 20201009
source: https://gist.github.com/jrivero/1085501
https://stackoverflow.com/questions/36445193/splitting-one-csv-into-multiple-files-in-python

Script for
1. Selecting  columns from SIRENE  and
2. Spliting csv files into smaller ones if necessary for geocoding
'''
#!/usr/bin/env python

import os

import csv
import itertools
from operator import itemgetter


def select_col_csv_byindex(csv_file, csv_out):
    '''
    Select column by index and save it
    '''
    delimiter = ','
    with open(csv_file, 'r') as input_file:
        reader = csv.reader(input_file, delimiter=delimiter)
        with open(csv_out, 'w',  newline='') as output_file:
            writer = csv.writer(output_file, delimiter=delimiter)
            writer.writerows(list(map(itemgetter('0, 5, 4, 7'), reader)))
            print('done selecting columns')

def select_col_csv_byname(csv_file, csv_out, headers):
    '''
    Select column by names and save it
    '''
    with open(csv_file, newline='') as rf:
        reader = csv.DictReader(rf, delimiter=',')
        with open(csv_out, 'w', newline='') as wf:
            writer = csv.DictWriter(wf, delimiter=',', extrasaction='ignore', fieldnames=headers)
            writer.writeheader()
            for row in reader:
               writer.writerow(row)
        print('done selecting columns')

def split(filehandler, delimiter=',', row_limit=10000,
          output_name_template=r'./input/sirene/chunks/sirene_%s.csv', output_path='.', keep_headers=True):
    """
    Splits a CSV file into multiple pieces.
    A quick bastardization of the Python CSV library.
    Arguments:

        `row_limit`: The number of rows you want in each output file. 10,000 by default.
        `output_name_template`: A %s-style template for the numbered output files.
        `output_path`: Where to stick the output files.
        `keep_headers`: Whether or not to print the headers in each output file.
    """
    import csv
    reader = csv.reader(filehandler, delimiter=delimiter)
    current_piece = 1
    current_out_path = os.path.join(
        output_path,
        output_name_template  % current_piece
    )
    current_out_writer = csv.writer(open(current_out_path, 'w', newline=''), delimiter=delimiter)
    current_limit = row_limit
    if keep_headers:
        headers = next(reader)
        current_out_writer.writerow(headers)
    for i, row in enumerate(reader):
        if i + 1 > current_limit:
            current_piece += 1
            current_limit = row_limit * current_piece
            current_out_path = os.path.join(
                output_path,
                output_name_template  % current_piece
            )
            current_out_writer = csv.writer(open(current_out_path, 'w', newline=''), delimiter=delimiter)
            if keep_headers:
                current_out_writer.writerow(headers)
        current_out_writer.writerow(row)

if __name__ == '__main__':

    csv_file = r'./input/sirene/SIRENE_201001_BasRhin.csv'
    headers = ['siren', 'siret', 'trancheEffectifsEtablissement', 'trancheEffectifsUniteLegale',
               'numeroVoieEtablissement', 'indiceRepetitionEtablissement',
               'typeVoieEtablissement', 'libelleVoieEtablissement', 'codePostalEtablissement',
               'libelleCommuneEtablissement', 'codeCommuneEtablissement', 'activitePrincipaleEtablissement']

    csv_out =r'./input/sirene/SIRENE_201001_BasRhin_columns.csv'

    #select_col_csv_byindex(csv_file,csv_out)
    select_col_csv_byname(csv_file, csv_out, headers)

    split(open(csv_out, 'r'))
