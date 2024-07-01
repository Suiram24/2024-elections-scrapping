"""
Web scrapper for the results of first round of the 2024 french legislatives elections
based on "https://www.resultats-elections.interieur.gouv.fr/legislatives2024/index.html" website.
This is a fork from https://github.com/Dogmael/elections-scrapping that has been updated

N.B. : A "result page" is a page contaning a table of results.
"""

import urllib.request
import csv
import pandas as pd
import numpy as np
import re

from bs4 import BeautifulSoup
from tkinter import *


def get_urls_departments(base_url):
    """Provides from the base page the pages all the departments pages.

    Args:
        base_url (string): Base election url where you can select the list of departments
        e.g. : "https://www.resultats-elections.interieur.gouv.fr/legislatives2024/ensemble_geographique/"

    Returns:
        list of string : List of urls corresponding to the districts list page for each departement of the index
        e.g. : ['https://www.resultats-elections.interieur.gouv.fr/legislatives2024/ensemble_geographique/84/01/index.html','https://www.resultats-elections.interieur.gouv.fr/legislatives2024/ensemble_geographique/32/02/index.html',..., 'https://www.resultats-elections.interieur.gouv.fr/legislatives2024/ensemble_geographique/./ZZ/index.html']
    """

    page = urllib.request.urlopen(base_url)
    soup = BeautifulSoup(page, 'html.parser')

    mydivs = soup.find("select",
                       {"class": "fr-select fr-col-9 sie-select-mobile"})

    results = [option['value'] for option in mydivs.find_all('option')]

    urls_depts = []

    for i in range(1,len(results)):
    
        urls_depts.append(
            "https://www.resultats-elections.interieur.gouv.fr/legislatives2024/ensemble_geographique/" +
            results[i])
            
    return urls_depts

def get_urls_circos(url_departement):
    """Provides a department page all the districts(circonsiptions in french) pages.

    Args:
        url_departement (string): Url corresponding to a department index 
        e.g. : "https://www.resultats-elections.interieur.gouv.fr/legislatives2024/ensemble_geographique/84/01/index.html"

    Returns:
        list of string : List of urls corresponding to the results page for each district of the index
        e.g. : ['https://www.resultats-elections.interieur.gouv.fr/legislatives2024/ensemble_geographique/84/01/0101/index.html','https://www.resultats-elections.interieur.gouv.fr/legislatives2024/ensemble_geographique/84/01/0102/index.html',..., 'https://www.resultats-elections.interieur.gouv.fr/legislatives2024/ensemble_geographique/./ZZ/11/index.html']
    """

    page = urllib.request.urlopen(url_departement)
    soup = BeautifulSoup(page, 'html.parser')

    mydivs = soup.find("select",
                       {"class": "fr-select fr-col-9 sie-select-mobile"})

    results = [option['value'] for option in mydivs.find_all('option')]

    urls_circos = []

    url_dept_root = url_departement.replace('index.html', '')

    for i in range(1,len(results)):
    
        urls_circos.append(
            url_dept_root +
            results[i])
            
    return urls_circos


def get_results_table(url):
    """Provides the results table from RESULTS PAGE of a district.

    Args:
        url (string): Url of a page with results table 
        e.g. : "https://www.resultats-elections.interieur.gouv.fr/legislatives2024/ensemble_geographique/84/01/0101/index.html"

    Returns:
        Pandas Dataframe object: Election results table
        e.g. : 

Circo     Liste des candidats     Nuance     Voix	% Inscrits	% Exprimés	Elu(e)	
7509	  Mme Sandrine ROUSSEAU	    UG	     26020	  36,48	       52,13	 OUI
7509	  Mme Pegah MALEK-AHMADI	ENS      11550 	  16,19        23,14     NON
    """


    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')

    table = soup.find(
        "table")
    
    circo = re.search(r'(\d+)/index\.html$', url).group(1)

    rows = []
    for row in table.find_all('tr')[1:]:  # Skip the header row
        cells = row.find_all('td')
        row_data = [cell.text.strip().replace('\u202f', '') for cell in cells]
        row_data.insert(0,circo)
        rows.append(row_data)

    headers = [header.text.strip() for header in table.find_all('th')]
    headers.insert(0, 'Circo')

    # Create a DataFrame
    df = pd.DataFrame(rows, columns=headers)

    return df
    

def process_all():
    url_dep = "https://www.resultats-elections.interieur.gouv.fr/legislatives2024/ensemble_geographique/index.html"
    urls_deps = get_urls_departments(url_dep)
    
    urls_circos = []

    for i in urls_deps:
        print(f"Parsing Departement : {i} \n")
        urls_circos = urls_circos + get_urls_circos(i)

    results = get_results_table(urls_circos[0])

    for i in urls_circos[1:]:
        try:
            results = pd.concat([results, get_results_table(i)])
        except:
            print(f"Issue with url : {i} \n")

    results.to_excel("Legislatives_2024_Tour1.xlsx")
    print("Scrapping finished. File saved.")
    return None

process_all()
#res = get_town_result('https://www.resultats-elections.interieur.gouv.fr/legislatives2024/ensemble_geographique/84/01/0101/index.html')
#res.to_excel("testindiv" + ".xlsx")
