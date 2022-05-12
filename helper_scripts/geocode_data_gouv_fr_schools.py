'''
author: sliz
data: 20201009
https://github.com/atao/BANO-Geocoder/blob/master/ban_geocoder.py
'''
#!/usr/bin/python
# -*- coding: utf-8 -*
import requests
import csv,os

import requests

def geocode(csv_input, out_csv):
    '''
    Geolocalise addresses via https://api-adresse.data.gouv.fr/search/csv/
    The size of an csv file must be smaller than 50 MB
    Check https://adresse.data.gouv.fr/csv#preview
    '''
    with open(out_csv, "wb") as csvFile:
        csvWrite = csv.writer(csvFile, delimiter=',', lineterminator='\n')

        data =(('columns', 'adresse'),
                ('columns', 'code_posta')
        )
        with open(csv_input, "rb") as fd:
            payoload = fd.read()
        r = requests.post(
               'https://api-adresse.data.gouv.fr/search/csv/',
                 files = {'data': ('filename.csv', payoload, 'text/csv')},
                data=data)
        if r.status_code != requests.codes.ok:
               r.raise_for_status()
        print(r.content)
        csvFile.write(r.content)

if __name__ == '__main__':

    #csv_input=r'X:\Groups\N41\GROUP-ORGA\MOBILITY_cluster\Activities\Smart_Charging\GIS_data\education\schools_address.csv'
    csv_input=r'X:\Groups\N41\GROUP-ORGA\MOBILITY_cluster\Activities\Smart_Charging\GIS_data\education\unis_address.csv'
    #out_csv =r'X:\Groups\N41\GROUP-ORGA\MOBILITY_cluster\Activities\Smart_Charging\GIS_data\education\schools_geo.csv'
    out_csv =r'X:\Groups\N41\GROUP-ORGA\MOBILITY_cluster\Activities\Smart_Charging\GIS_data\education\unis_goe.csv'
    geocode(csv_input, out_csv)
