import itertools, operator, urllib.request

from bs4 import BeautifulSoup

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
        cols = [element.text.strip() for element in tmp_cols]
        parsing_list = [element for element in cols if cols.index(element) != 2]
        all_scheldules.append([element for element in parsing_list if element])

    all_scheldules_remove_duplicates = list(set(map(lambda i: tuple(i), all_scheldules)))

    return all_scheldules_remove_duplicates

def new_text_view(result_list):

    new_list = []

    tmp_list = [list(element) for element in result_list]

    i = 1
    for element in tmp_list:
        element.insert(0, f'*{i}* \U0001F689')
        i += 1

    for element in tmp_list:
        new_list.append(list(map(operator.add, itertools.cycle(('', '*Номер поїзда*: ', '*Назва поїзда*: ',
            '*Час прибуття*: ', '*Час відправки*: ')), element)))
        new_list.append('\n')

    result = [list(itertools.chain.from_iterable(itertools.islice(new_list, i, i + 6))) for i in
              range(0, len(new_list), 6)]

    return result



# if __name__ == '__main__':
#     now = datetime.now()
#     search_date = now.strftime("%d.%m.%Y")
#     search_city = 'Odessa'
#     print(new_text_view(parsing_result(search_city, search_date)))
