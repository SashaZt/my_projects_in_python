from requests import get
from bs4 import BeautifulSoup
from json import loads, dumps, load
from csv import DictWriter
import threading
from os import listdir, remove
from configparser import ConfigParser
import pandas as pd
import warnings

parser = ConfigParser()
parser.read('config.cfg')
api_key = parser['Configuration']['API_KEY']
threads_count = int(parser['Configuration']['ThreadsCount'])
not_parsed_urls = []
warnings.simplefilter(action='ignore', category=FutureWarning)


def parse_to_json(url, page, url_param):
    if page == 1:
        url_param = ''
        page = ''
    full_url = f'{url}{url_param}{page}'
    for _ in range(2):
        try:
            with get('http://api.scraperapi.com', params={'api_key': api_key, 'url': full_url}) as resp:
                if page == '':
                    page = 1
                if resp.status_code == 403:
                    print('Закончились кредиты. Оплати тариф на http://api.scraperapi.com')
                    input()
                    exit()
                elif resp.status_code != 200:
                    not_parsed_urls.append(full_url)
                    print(f'Не получилось спарсить страницу {page}. Попробую спарсить ее позже...')
                    return
                else:
                    print(f'Успешно спарсена страница {page}')
                    for i in BeautifulSoup(resp.text, 'html.parser').find_all('script', {'type': 'application/json'}):
                        json_ = loads(i.text)
                        if isinstance(json_, dict):
                            if json_.get('__listing_StoreState'):
                                json_ = loads(json_.get('__listing_StoreState'))
                                if json_.get('items'):
                                    with open(f'temp/page-{page}.json', 'w', encoding='utf8') as f:
                                        f.write(dumps(json_))
                                return
        except:
            pass


def parse_not_parsed_urls(url):
    page = url.split('p=')
    if len(page) > 1:
        page = page[1]
    else:
        page = 1
    for _ in range(2):
        try:
            with get('http://api.scraperapi.com', params={'api_key': api_key, 'url': url}) as resp:
                if page == '':
                    page = 1
                if resp.status_code == 403:
                    print('Закончились кредиты. Оплати тариф на http://api.scraperapi.com')
                    input()
                    exit()
                elif resp.status_code != 200:
                    print(f'Не получилось спарсить страницу {page}. Попробую спарсить ее позже...')
                    return
                else:
                    print(f'Успешно спарсена страница {page}')
                    not_parsed_urls.remove(url)
                    for i in BeautifulSoup(resp.text, 'html.parser').find_all('script', {'type': 'application/json'}):
                        json_ = loads(i.text)
                        if isinstance(json_, dict):
                            if json_.get('__listing_StoreState'):
                                json_ = loads(json_.get('__listing_StoreState'))
                                if json_.get('items'):
                                    with open(f'temp/page-{page}.json', 'w', encoding='utf8') as f:
                                        f.write(dumps(json_))
                                return
        except:
            pass


def write_items(items, csv_writer):
    for item in items['items']['elements'][::]:
        try:
            write_info = {'id': item['id'],
                          'url': item['url'],
                          'title': item['title']['text'],
                          'images': ';'.join(i['medium'] for i in item['photos']),
                          'price': item['price']['normal']['amount'],
                          'seller': item['seller']['login'],
                          'Stan': '-',
                          'Numer katalogowy części': '-',
                          'Producent części': '-'
                          }

            for param in item['parameters']:
                if param['name'] == 'Stan':
                    write_info['Stan'] = param['values'][0]
                elif param['name'] == 'Numer katalogowy części':
                    write_info['Numer katalogowy części'] = param['values'][0]
                elif param['name'] == 'Producent części':
                    write_info['Producent części'] = param['values'][0]
            csv_writer.writerow(write_info)
        except:
            try:
                write_info = {'id': item['offerId'],
                              'url': item['url'],
                              'title': item['title']['text'],
                              'images': ';'.join(i['medium'] for i in item['photos']),
                              'price': item['price']['normal']['amount'],
                              'seller': '-',
                              'Stan': '-',
                              'Numer katalogowy części': '-',
                              'Producent części': '-'
                              }

                for param in item['parameters']:
                    if param['name'] == 'Stan':
                        write_info['Stan'] = param['values'][0]
                    elif param['name'] == 'Numer katalogowy części':
                        write_info['Numer katalogowy części'] = param['values'][0]
                    elif param['name'] == 'Producent części':
                        write_info['Producent części'] = param['values'][0]
                csv_writer.writerow(write_info)
            except:
                pass
            pass


def convert_json_to_csv():
    print('Записываю информацию в csv файл...')
    keys = ['id', 'title', 'url', 'images', 'price', 'seller',
            'storona zabydovi', 'Stan',
            'Numer katalogowy części', 'Producent części']
    writer = DictWriter(open('new.csv', 'w', encoding='utf16', newline=''), keys, delimiter='\t')
    writer.writerow({i: i for i in keys})
    for i in listdir('temp'):
        try:
            write_items(load(open('temp/' + i, encoding='utf-8')), writer)
        except:
            pass


def sort_table():
    df1 = pd.DataFrame(columns=[
        'id',
        'title',
        'url',
        'images',
        'price',
        'seller',
        'storona zabydovi',
        'Stan',
        'Numer katalogowy części',
        'Producent części'
    ])
    df1 = df1.fillna("")
    df1 = df1.astype(str)

    df = pd.read_csv('new.csv', sep='\t', encoding='utf-16')
    df = df.sort_values(by=['price'])
    for i, row in df.iterrows():
        if row['Numer katalogowy części'] == '-':
            new_row = pd.DataFrame([{
                'id': row['id'],
                'title': row['title'],
                'url': row['url'],
                'images': row['images'],
                'price': row['price'],
                'seller': row['seller'],
                'storona zabydovi': row['storona zabydovi'],
                'Stan': row['Stan'],
                'Numer katalogowy części': row['Numer katalogowy części'],
                'Producent części': row['Producent części']
            }])
            df1 = pd.concat([df1, new_row], ignore_index=True)

    df = df.loc[df['Numer katalogowy części'] != '-']
    df.drop_duplicates(subset=['Numer katalogowy części'], inplace=True)
    df = pd.concat([df, df1], ignore_index=True)
    df.to_csv('new.csv', sep='\t', index=False, encoding='utf-16')


def parse(url, page1, page2):
    # format url for parsing
    url_param = ''
    if len(url.split('?string=')) > 1:
        url_param = '&p='
    else:
        url_param = '?p='

    page = int(page1)
    last_page = int(page2)
    num_pages = int(last_page - page)
    if num_pages == 0:
        num_pages = 1
    print(f'Все страницы: {num_pages}')

    is_last_page = False
    threads = []
    while not is_last_page:
        for i in range(threads_count):
            if i >= len(threads):
                thread = threading.Thread(target=parse_to_json, args=(url, page, url_param,))
                thread.start()
                threads.append(thread)
                print(f'Страница {page}/{last_page} парсится')
                page += 1
            elif not threads[i].is_alive():
                thread = threading.Thread(target=parse_to_json, args=(url, page, url_param,))
                thread.start()
                threads[i] = thread
                print(f'Страница {page}/{last_page} парсится')
                page += 1

            if page > last_page:
                is_last_page = True
                break

    for thread in threads:
        if thread.is_alive():
            thread.join()

    if len(not_parsed_urls) > 0:
        print('Начинаю парсить не спарсенные раннее ulrs...')
        while len(not_parsed_urls) > 0:
            parse_again()
    print('Все страницы успешно спарсены!')


def parse_again():
    last_page = len(not_parsed_urls)
    print(f'Страницы для повторного парсинга: {last_page}')

    page = 1
    is_last_page = False
    threads = []
    while not is_last_page:
        for i in range(threads_count):
            if i >= len(threads):
                thread = threading.Thread(target=parse_not_parsed_urls, args=(not_parsed_urls[i],))
                thread.start()
                threads.append(thread)
                print(f'Страница {page}/{last_page} парсится')
                page += 1
            elif not threads[i].is_alive():
                thread = threading.Thread(target=parse_not_parsed_urls, args=(not_parsed_urls[i],))
                thread.start()
                threads[i] = thread
                print(f'Страница {page}/{last_page} парсится')
                page += 1

            if page > last_page:
                is_last_page = True
                break

    for thread in threads:
        if thread.is_alive():
            thread.join()


def clear_temp_folder():
    for i in listdir('temp'):
        remove(f'temp/{i}')


if __name__ == '__main__':
    url = None
    pages = None
    try:
        with open('url.txt') as f:
            url = f.read()
    except Exception as e:
        pass

    if not url:
        url = input('Укажите url для парсинга: ')
    start_page = input('Укажите первую страницу для парсинга: ')
    final_page = input('Укажите последнюю страницу для парсинга: ')
    print(f'Начинаю парсинг {url}')
    clear_temp_folder()
    parse(url, start_page, final_page)
    convert_json_to_csv()
    sort_table()
    input('Парсинг успешно окончен!')
