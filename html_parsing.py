import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from collections import OrderedDict

import urllib.request


names = dict()
names['train_number'] = 0
names['train_name'] = 1
names['train_period'] = 2
names['train_arrived'] = 3
names['train_departure'] = 4

def parsing_result(search_city: str, search_date: str):
    pars_file = urllib.request.urlopen(f'https://gd.tickets.ua/uk/railwaytracker/table/{search_city}/{search_date}')
    pars_bytes = pars_file.read()

    pars_str = pars_bytes.decode('utf8')
    pars_file.close()

    soup = BeautifulSoup(pars_str, 'lxml')

    all_scheldules = []
    table = soup.find('table', class_='schedules_table')
    table_body = soup.find('tbody')

    rows = table_body.find_all('tr')
    for row in rows:
        tmp_cols = row.find_all('td')
        cols = [ele.text.strip() for ele in tmp_cols]
        # tmp_list = [ele for ele in cols if ele]
        parsing_list = [ele for ele in cols if cols.index(ele) != 2]
        # for ele in cols:
        #     if ele not in all_scheldules  and cols.index(ele) != 2:
        #         all_scheldules.append([ele])
        all_scheldules.append([ele for ele in parsing_list if ele not in all_scheldules])

    return all_scheldules


if __name__ == '__main__':
    now = datetime.now()
    search_date = now.strftime("%d.%m.%Y")
    search_city = 'Odessa'
    print(parsing_result(search_city, search_date))
