File written by Jordan

# ETAPE 1: GEOCODAGE DATAGOUV #
###############################

# Le fichier SIREN_**_DEPT67 a été découpé en 16 fichiers de 10000 lignes avec cvssplitter.
# .. liste des fichiers:(sirene_201702_stock_DEPET67.000, ..., sirene_201702_stock_DEPET67.015)

# Les fichiers ont été ensuite géocodés avec le géocodeur: https://adresse.data.gouv.fr/csv/
    # Il y a aussi possibilité d'utiliser l'API! https://adresse.data.gouv.fr/api/
# .. selon les variables L4_NORMALISEE(NUM+RUE), L6_NORMALISEE(COMMUNE+CP), et L7 NORMALISEE(FRANCE)
# .. liste des fichiers:(sirene_201702_stock_DEPET67.000.geocoded.csv, ..., sirene_201702_stock_DEPET67.015.geocoded.csv)
# Les colonnes ajoutées sont:
    # latitude
    # longitude
    # result_label: l'adresse complète
    # result_score: le score
    # result_type: housenumber ou street, ou locality
    # result_id
    # result_housenumber: numéro
    # result_name: rue
    # result_street: VIDE?
    # result_postcode
    # result_city
    # result_context: "67, Bas-Rhin, Grand-Est (Alsace)"
    # result_citycode

EN
#
# The file SIREN_**_DEPT67 was cut into 16 files of 10000 lines with cvssplitter. # . . list of files: (sirene_201702_stock_DEPET67. 000,. . . , sirene_201702_stock_DEPET67. 015)

# The files were then geocoded with the geocoder: Https://adresse. data. gouv. fr/csv/
# There is also the possibility to use the API! https://adresse. data. gouv. fr / IPA - International Phonetic Alphabet /
# . . according to variables L4_NORMALISEE (NUM + RUE), L6_NORMALISEE (COMMUNE + CP), and L7 NORMALISEE (FRANCE)
# . . list of files: (sirene_201702_stock_DEPET67. 000. geocoded. csv,. . . , sirene_201702_stock_DEPET67. 015. geocoded. csv)
# The columns added are:
# degree of latitude
# degree of longitude
# result_label: the full address
# result_score: the score
# result_type: housenumber or street, or locality
# result_id
# result_housenumber: number
# result_name: street
# result_street: VIDE? # result_postcode
# result_city
# result_context: "67, Bas-Rhin, Grand-Est (Alsace)"
# result_citycode

####

Le fichier sirene_201702_stock_DEPET67_geocoded.csv, est l'agrégations de ces 16 fichiers géocodés pas DATAGOUV.
# EN: The file sirene_201702_stock_DEPET67_geocoded. csv, is the aggregations of these 16 geocoded files not DATAGOUV

# ETAPE 2: GEOCODAGE GOOGLE #
#############################

On utilise le géocodage de google pour les adresses que DATAGOUV n'a pas su géocoder (1387/159146=0.9%)
Ces lignes sont stockées dans le fichier "sirene_201702_stock_DEPET67_google_geocoded.csv"
Google a su géocoder 435/1387=31% des adresses.

EN: Google geocoding is used for addresses that DATAGOUV has not been able to geocode (1387/159146 = 0. 9 %)
These lines are stored in the file "sirene_201702_stock_DEPET67_google_geocoded. csv"
Google has been able to geocode 435/1387 = 31 % addresses

# ETAPE 3: AGGREGATION #
########################

On recole les géocodages DATAGOUV et GOOGLE réussis. 158711/159146=99.7%
Ce fichier n'est pas enregistré.
EN: Successful geocoding DATAGOUV and GOOGLE are collected. 158711 / 159146=99. 7 %
This file is not saved.

# ETAPE 4: IRIS #
#################

On fait une jointure spatiale en R afin de récupérer les IRIS associés aux coordonnées, 
La procédure échoue pour 89/158711=0.06% coordonnées. On garde donc 158622 lignes.
les résultats sont stockés dans le fichier:
"sirene_201702_stock_DEPET67_geocoded_IRIS.csv"
On stock aussi une version "LIGHT" de ce fichier, avec 24/105 colonnes sélectionnées:
"sirene_IRIS_LIGHT.csv"

EN: A spatial join is made in R in order to recover the IRIS associated with the coordinates,
The procedure fails for 89/158711 = 0. 06 % coordinates. So 158,622 lines are kept. the results are stored in the file:
"sirene_201702_stock_DEPET67_geocoded_IRIS. csv"
We also stock a "LIGHT" version of this file, with 24/105 columns selected:
"sirene_IRIS_LIGHT. csv"

Les colonnes sont:
# Fichier SIRENE
- SIREN, #Identifiant de l'entreprise
- NIC, #Numéro interne de classement de l'établissement
- L4_NORMALISEE, #Quatrième ligne de l’adressage de l’établissement
- L6_NORMALISEE, #Sixième ligne de l’adressage de l’établissement
- LIBCOM, #Libellé de la commune de localisation de l'établissement
- APET700, #Activité principale de l'établissement <- TRES IMPORTANTS POUR l'ATTRACTIVITE
- LIBAPET, #Libellé de l'activité principale de l'établissement
- TEFET, #Tranche d'effectif salarié de l'établissement
- LIBTEFET #Libellé de la tranche d'effectif de l'établissement
- TEFEN, #Tranche d'effectif salarié de l'entreprise
- LIBTEFEN, #Libellé de la tranche d'effectif de l'entreprise
# GEOCODAGE
- latitude, 
- longitude, 
- result_label, #adresse trouvée par le geocodage DATAGOUV/GOOGLE
- result_score, #Score pour le geocodage DATAGOUV
- result_postcode, 
- result_city, 
- result_citycode, #citycode du géocodage DATAGOUV
# JOINTURE SPATIALE POUR IRIS
- INSEE_COM, #citycode de la jointure spatial
- NOM_COM,
- IRIS,	
- CODE_IRIS,	
- NOM_IRIS,
- TYP_IRIS

EN:
The columns are:
# SIRENE file
- SIREN, # Company ID
- NIC, # Institution's internal classification number
- L4_NORMALISEE, # Fourth line of the address of the establishment
- L6_NORMALISEE, # Sixth line of the address of the establishment
- LIBCOM, # Wording of the locating municipality of the establishment
- APET700, # Main activity of the establishment < - TRES IMPORTANTS FOR ATTRACTIVENESS
- LIBAPET, # Wording of the institution's main activity
- TEFET, # Employee share of the establishment
- LIBTEFET # Wording of the institution's staff bracket
- TEFEN, # Employee share of the company
- LIBTEFEN, # Wording of the company's share of employees
# GEOCODAGE
- degree of latitude,
- degree of longitude,
- result_label, # address found by the geocoding DATAGDE/GOOGLE
- result_score, # Score for geocoding DATAGOUV
- result_postcode,
- result_city,
- result_citycode, # citycode of geocoding DATAGOUV
# SPACE ATTACHMENT FOR IRIS
- INSEE_COM, # citycode of the space join
- NOM_COM,
- IRIS,
- CODE_IRIS,
- NOM_IRIS,
- TYP_IRIS

