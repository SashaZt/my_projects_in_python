from requests import get
from bs4 import BeautifulSoup
from json import loads, dumps, load
from csv import DictWriter
import threading
import time
from os import listdir, remove
from configparser import ConfigParser

parser = ConfigParser()
parser.read('config.cfg')
api_key = parser['Configuration']['API_KEY']
threads_count = int(parser['Configuration']['ThreadsCount'])


def write_in_csv(url, page):
    for _ in range(2):
        try:
            with get('http://api.scraperapi.com', params={'api_key': api_key,
                                                          'url': f'{url}?p={page}'}) as resp:
                if resp.status_code == 403:
                    print('Pay https://www.scraperapi.com/pricing/')
                    input()
                    exit()
                elif resp.status_code == 500:
                    continue
                elif resp.status_code != 200:
                    return
                else:
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


def get_last_page(url):
    # 2 tries for get
    for _ in range(2):
        with get('http://api.scraperapi.com', params={'api_key': api_key,
                                                      'url': f'{url}'}) as resp:
            if resp.status_code == 403:
                print('Pay https://www.scraperapi.com/pricing/')
                input()
                exit()
            elif resp.status_code == 500:
                continue
            elif resp.status_code != 200:
                return
            else:
                for i in BeautifulSoup(resp.text, 'html.parser').find_all('script', {'type': 'application/json'}):
                    json_ = loads(i.text)
                    if isinstance(json_, dict):
                        if json_.get('props'):
                            last_page = json_['props']['searchMeta']['lastAvailablePage']
                            return int(last_page)


def write_items(items, csv_writer):
    for item in items['items']['elements'][1:]:
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


def convert_json_to_csv():
    keys = ['id', 'title', 'url', 'images', 'price', 'seller',
            'storona zabydovi', 'Stan',
            'Numer katalogowy części', 'Producent części']
    writer = DictWriter(open('new_csv.csv', 'w', encoding='utf16', newline=''), keys, delimiter='\t')
    writer.writerow({i: i for i in keys})
    for i in listdir('temp'):
        try:
            write_items(load(open('temp/' + i, encoding='utf-8')), writer)
        except:
            pass


def parse(url):
    #last_page = get_last_page(url)
    last_page = 2
    print(f'All pages: {last_page}')

    page = 1
    is_last_page = False
    threads = []
    while not is_last_page:
        for i in range(threads_count):
            if i >= len(threads):
                thread = threading.Thread(target=write_in_csv, args=(url, page,))
                thread.start()
                threads.append(thread)
                print(f'Page {page}/{last_page} parsing')
                page += 1
            elif not threads[i].is_alive():
                thread = threading.Thread(target=write_in_csv, args=(url, page,))
                thread.start()
                threads[i] = thread
                print(f'Page {page}/{last_page} parsing')
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
    try:
        with open('url.txt') as f:
            url = f.read()
    except Exception as e:
        pass

    if not url:
        url = input('Input sellers url: ')
    print(f'Start parsing {url}')
    clear_temp_folder()
    parse(url)
    convert_json_to_csv()
    input('Parsing end')
