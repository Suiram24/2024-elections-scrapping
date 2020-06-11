"""
Web scrapper for the results of first round of the 2020 french municipal elections
based on "https://elections.interieur.gouv.fr/municipales-2020" website.

Warrning : French Polynesia is excluded from the results.

N.B. : A "result page" is a page contaning a table of results.
"""

import urllib.request
import csv
import pandas as pd
import numpy as np
import re

from bs4 import BeautifulSoup
from tkinter import *


def get_urls_by_letter(url_dep):
    """Provides from a department's page the pages corresponding to the departement's city indexes (one page of index per letter).

    Args:
        url_dep (string): url corresponding to a departement 
        e.g. : "https://elections.interieur.gouv.fr/municipales-2020/080/index.html"

    Returns:
        list of strings: list of urls of city indexes
        e.g. : ['https://elections.interieur.gouv.fr/municipales-2020/080/080A.html', 'https://elections.interieur.gouv.fr/municipales-2020/080/080T.html',..., 'https://elections.interieur.gouv.fr/municipales-2020/080/080Y.html']
    """
    
    page = urllib.request.urlopen(url_dep)
    soup = BeautifulSoup(page, 'html.parser')
    mydivs = soup.findAll("a")

    urls_letter = []
    for i in range(len(mydivs[1:-2])):
        urls_letter.append(
            "https://elections.interieur.gouv.fr/municipales-2020" +
            mydivs[2 + i].get('href')[2:])

    return urls_letter


def get_urls_towns(url_index_by_letter):
    """Provides from the page corresponding to a city index the pages corresponding to the cities of the index.

    Args:
        url_index_by_letter (string): Url corresponding to a city index 
        e.g. : "https://elections.interieur.gouv.fr/municipales-2020/080/080G.html"

    Returns:
        list of string : List of urls corresponding to the results page for each city of the index
        e.g. : ['https://elections.interieur.gouv.fr/municipales-2020/080/080373.html','https://elections.interieur.gouv.fr/municipales-2020/080/080374.html',..., 'https://elections.interieur.gouv.fr/municipales-2020/080/080403.html']
    """

    page = urllib.request.urlopen(url_index_by_letter)
    soup = BeautifulSoup(page, 'html.parser')

    mydivs = soup.find("table",
                       {"class": "table table-bordered tableau-communes"})

    results = mydivs.findAll('td')

    urls_towns = []

    for i in range(len(results)):
    
        if (i % 3 == 2 and results[i].getText() != 'Aucun résultat reçu'):
            urls_towns.append(
                "https://elections.interieur.gouv.fr/municipales-2020" +
                results[i].find("a").get('href')[2:])
            
    return urls_towns


def get_urls_sector(url):
    """Provides urls of sector's results pages.
    Use this function for cities with districts (Paris, Lyon, Marseille). 

    Args:
        url (string): Url of a city with districs 
        e.g. : "https://elections.interieur.gouv.fr/municipales-2020/013/013055.html"

    Returns:
        List of strings: List of urls for city sectors results page.
        e.g. : ['https://elections.interieur.gouv.fr/municipales-2020/013/013055SR01.html','https://elections.interieur.gouv.fr/municipales-2020/013/013055SR02.html',...,'https://elections.interieur.gouv.fr/municipales-2020/013/013055SR08.html']
    """

    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')
    mydivs = soup.find("table",{"class": "table table-bordered tableau-candidats"})
    mydivs = mydivs.find_all("a")

    urls_sector = []

    for divs in mydivs:
        urls_sector.append(
            "https://elections.interieur.gouv.fr/municipales-2020" +
            divs.get('href')[2:])

    return urls_sector


def get_location(soup):
    """Provides departement (or secteur for city with arrondissements) name and city name from a results page.

    Args:
        soup (soup object from BeautifulSoup library): Soup from a results page

    Returns:
        list of two strings : ["département name (number off departement)", "city name"] 
        e.g. : ['Rhône (69)', 'Marcy']
    """

    location = soup.find("div", {"class": "row-fluid pub-resultats-entete"})
    location = location.find("h3")
    location = location.getText()
    location = location.replace('\n', '').replace('\t', '')
    location = re.split(" - ", location)

    return location


def get_results_table(url):
    """Provides the results table from RESULTS PAGE (!= a city).

    Args:
        url (string): Url of a page with results table (this could be a page of a city or of a sector)
        e.g. : "https://elections.interieur.gouv.fr/municipales-2020/013/013003.html"

    Returns:
        Pandas Dataframe object: Election results table
        e.g. : 

Département	            Commune     Type de scruttin	Candidats	Voix	% Inscrits	% Exprimés	Elu(e)	Liste conduite par	Voix	% inscrits	% exprimés	Sièges au conseil municipal / conseil de secteur	Sièges au conseil communautaire											
Bouches-du-Rhône (13) 	Alleins	    listes électorales	NaN	        NaN	    NaN	        NaN	        NaN	    M. Philippe GRANGE	829	    37,97	    66,05	    19	                                                1
                        Alleins	    listes électorales	NaN	        NaN 	NaN     	NaN	        NaN 	M. Daniel JUVIGNY	426	    19,51	    33,94	    4       	                                        0  
    """

    table = pd.DataFrame(columns=[
        "Département", "Commune", "Type de scruttin", "Candidats", "Voix",
        "% Inscrits", "% Exprimés", "Elu(e)", "Liste conduite par", "Voix",
        "% inscrits", "% exprimés",
        "Sièges au conseil municipal / conseil de secteur",
        "Sièges au conseil communautaire"
    ])

    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')

    mydivs = soup.find(
        "table", {"class": "table table-bordered tableau-resultats-listes"})

    if (mydivs != None):  #First case: we have electoral lists.
        nb_columns = mydivs.findAll('tr')[0].getText()[:-1].count(
            "\n"
        )  #We will use it to manage cases where we do not have a community council (e.g. : Lyon sector 1)
        results = mydivs.findAll('td')
        candidat = []
        
        for i in range(len(results)):
            candidat.append(results[i].getText())
            
            if (i % (nb_columns) == nb_columns - 1):  #We are coming to the end of a candidate
                table.loc[i // 6] = get_location(soup) + [
                    "listes électorales"
                ] + [np.nan] * 5 + candidat + (6 - nb_columns) * [np.nan]
                candidat = []
    else:  # Second case: we have a majority vote.
        mydivs = soup.find(
            "table", {"class": "table table-bordered tableau-resultats-maj"})
        results = mydivs.findAll('td')
        candidat = []
        
        for i in range(len(results)):
            candidat.append(results[i].getText())
            
            if (i % 5 == 4):  #We are coming to the end of a candidate
                table.loc[i // 5] = get_location(soup) + ["scrutin majoritaire"] + candidat + [np.nan] * 6
                candidat = []
                
    table.set_index(["Département", "Commune"], inplace=True)

    return table


def get_town_result(url):
    """Provides the election results for a city.

    Args:
        url (string): Url of a page corresponding to a city.
        e.g. : "https://elections.interieur.gouv.fr/municipales-2020/013/013A.html"

    Returns:
        Pandas DataFrame object: Table of results. If there are several sectors in the city, the table contains them all.
    """

    urls_cities_with_arrondissements = [
        "https://elections.interieur.gouv.fr/municipales-2020/069/069123.html",
        "https://elections.interieur.gouv.fr/municipales-2020/075/075056.html",
        "https://elections.interieur.gouv.fr/municipales-2020/013/013055.html"
    ]

    if (url in urls_cities_with_arrondissements):
        urls_sector = get_urls_sector(url)
        results = pd.DataFrame()
        
        for url in urls_sector:
            results = pd.concat([results, get_results_table(url)])
    else:
        results = get_results_table(url)

    return results


def main():
    """Scrape a department and save the result in an exel array whose name specifies.

    Returns:
        None
    """

    departements_list = ["%d" % i for i in range(1, 20)] + ["2A", "2B"] + ["%d" % i for i in range(21, 96)] + ["%d" % i for i in range(971, 977)] + ["988"]  #Beware of Corsica which replaces department number 20 with 2A and 2B
    departement_number = input(
        "Enter the number of the department for which you want to retrieve the data \n e.g. 75:"
    )
    file_name = input("Under what name do you want to save the result?")

    #Check input

    if (departement_number not in departements_list):
        print("The departement number is incorect.")
        return None

    if re.search(r'[^A-Za-z0-9_\-\\]', file_name):
        print("Incorrect file name.")
        return None

    #Generate departement url

    try:
        departement_number = "%03d" % int(departement_number)
    except:  #for Corse which number is 2A and 2B
        departement_number = "0" + departement_number

    #

    if(departement_number == 75):  #Paris is a specific case, actually it's simultanously a departement and a city.
        results = get_town_result(
            "https://elections.interieur.gouv.fr/municipales-2020/075/075056.html"
        )
        results.to_excel(file_name + ".xlsx")
        print("Scrapping finished. File saved.")
    else:
        url_dep = "https://elections.interieur.gouv.fr/municipales-2020/" + departement_number + "/index.html"
        urls_letter_index = get_urls_by_letter(url_dep)
        
        urls_towns = []

        for i in urls_letter_index:
            urls_towns = urls_towns + get_urls_towns(i)

        results = get_town_result(urls_towns[0])

        for i in urls_towns[1:]:
            try:
                results = pd.concat([results, get_town_result(i)])
            except:
                print(f"Issue with url : {i} \n")

        results.to_excel(file_name + ".xlsx")
        print("Scrapping finished. File saved.")
        return None
