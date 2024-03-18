import csv
import os
import re
import time
from typing import List, Dict
import requests


bad_url = []
cookies = {
    'ak_bmsc': 'EA9961D4BA849D3AC4CB97CC1C162EA6~000000000000000000000000000000~YAAQDQxAFw0pm9uIAQAAMY6F3RRnVuXFv4jC/DzpcHz8wr4R5Jtr5VTNvGrch9m1g/NzHfRG3zxgATE+LCELn1HESJumYUgLV9nECNF7wGzlRLAhrc7U4P2CQXAVXjEUEemBowLkRk6umFmr/GgGoD9TswWMtSx6mAxUJTuk4DZ4YxEr2ebl7no7YGAWMv5Jeno0qlyI+5m4+JXttGPtupH6rkFwtL2JckEUkKklgQuFAo9jJeZVN+bUhpZ0njZCWWduOGZHr4/AYqb52LGMb5T4q3tdOeXCKGCCdIsupUJTsa6VLSwPyyFURrgns+T/kHnkJMHDTUBcOAtZmhNz1AotifjdjYN+HOJ5ddKwNXwdBgvL3SOiK/oWvCvtC7pZTo/TAiLhrq53',
    'bm_mi': '358A0D18C4DAD9BFA09771FC5AB403C4~YAAQDQxAF60wnNuIAQAAv4GJ3RRjWk57jfsblbuIKwMwsO5DBEnts97/tCHs4oTJ2WG9etYkQA+UjHbplreoaacyd11aa1J1bpbf41cbq3FZ2vpr4Q/tjEIvyonyYO//NYGCkRFufc1CSay0el9XXBXkS30kehveHX2xwsTNDFwJxXI+ffwIxDVWLQv6lypazcpvnlAPpHTPRSg+UrLQ6Zgmw5AsbJF139jLNlOaozuvPJzaViygYhHFnG4QM+fLp8G7sH1zUpQLFAx0QUoWSJEqSb/g6ow09hE1qOBnnIVWU7KCjScTzrMQfg9otIgGWq6AWUEcogaJ9EyWIxf9p9X8enHw~1',
    'bm_sv': '8D7D22C834C4108B2E3B28CCD234DE6C~YAAQDQxAF64wnNuIAQAAv4GJ3RS2BqJNjwW50vYdaE7tC3qz6poW/tZglurMfsps6OSDO6k7t6/pNCtK7SH+GEpHXhoogIHaiTsM/wRXxP0kCFBVFkLwjcjfRizsE+aP9L2rJnNhCfW0Tz77ZfYidkFcSiVjCF5wYs+cFNKDdbfXdrLYvN8GRBlrivyyZsaJlRHqBBEbxX5HRizu8FNh3qJgyGWMk4xkxbD5DlCkurmyMXfNtRdPy51QfQSfAI4=~1',
}

headers = {
    'authority': 'www.tesla.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'ak_bmsc=EA9961D4BA849D3AC4CB97CC1C162EA6~000000000000000000000000000000~YAAQDQxAFw0pm9uIAQAAMY6F3RRnVuXFv4jC/DzpcHz8wr4R5Jtr5VTNvGrch9m1g/NzHfRG3zxgATE+LCELn1HESJumYUgLV9nECNF7wGzlRLAhrc7U4P2CQXAVXjEUEemBowLkRk6umFmr/GgGoD9TswWMtSx6mAxUJTuk4DZ4YxEr2ebl7no7YGAWMv5Jeno0qlyI+5m4+JXttGPtupH6rkFwtL2JckEUkKklgQuFAo9jJeZVN+bUhpZ0njZCWWduOGZHr4/AYqb52LGMb5T4q3tdOeXCKGCCdIsupUJTsa6VLSwPyyFURrgns+T/kHnkJMHDTUBcOAtZmhNz1AotifjdjYN+HOJ5ddKwNXwdBgvL3SOiK/oWvCvtC7pZTo/TAiLhrq53; bm_mi=358A0D18C4DAD9BFA09771FC5AB403C4~YAAQDQxAF60wnNuIAQAAv4GJ3RRjWk57jfsblbuIKwMwsO5DBEnts97/tCHs4oTJ2WG9etYkQA+UjHbplreoaacyd11aa1J1bpbf41cbq3FZ2vpr4Q/tjEIvyonyYO//NYGCkRFufc1CSay0el9XXBXkS30kehveHX2xwsTNDFwJxXI+ffwIxDVWLQv6lypazcpvnlAPpHTPRSg+UrLQ6Zgmw5AsbJF139jLNlOaozuvPJzaViygYhHFnG4QM+fLp8G7sH1zUpQLFAx0QUoWSJEqSb/g6ow09hE1qOBnnIVWU7KCjScTzrMQfg9otIgGWq6AWUEcogaJ9EyWIxf9p9X8enHw~1; bm_sv=8D7D22C834C4108B2E3B28CCD234DE6C~YAAQDQxAF64wnNuIAQAAv4GJ3RS2BqJNjwW50vYdaE7tC3qz6poW/tZglurMfsps6OSDO6k7t6/pNCtK7SH+GEpHXhoogIHaiTsM/wRXxP0kCFBVFkLwjcjfRizsE+aP9L2rJnNhCfW0Tz77ZfYidkFcSiVjCF5wYs+cFNKDdbfXdrLYvN8GRBlrivyyZsaJlRHqBBEbxX5HRizu8FNh3qJgyGWMk4xkxbD5DlCkurmyMXfNtRdPy51QfQSfAI4=~1',
    'dnt': '1',
    'pragma': 'no-cache',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}

def get_page(url):
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False
    })
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    """Get page by url"""
    try:
        response = requests.get(url, cookies=cookies, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            bad_url.append(url)
            with open(f'c:\\asics_pl\\csv_url\\{category}\\bad_url.csv', "a",
                      newline='', errors='ignore') as file:
                writer = csv.writer(file)
                writer.writerow(bad_url)
            return None
    except requests.exceptions.RequestException as e:
        print(e)
        return None


def save_html(html, counter, category):
    """Save the html page with the given counter and category"""
    filename = f"c:\\asics_pl\\html_product\\{category}\\0_{counter}.html"
    with open(filename, "w", encoding='utf-8') as f:
        f.write(html)


def process_url(url, counter, category):
    """Process url to get page and save as html"""
    if re.match(r'^https?://', url):
        html = get_page(url)
        if html is not None:
            save_html(html, counter, category)
def check_bad_url_file(category):
    retry_count = 0
    while retry_count < 3:
        """Check if bad_url.csv exists, rename it to url.csv and remove it if it exists"""
        if os.path.isfile(f'c:\\asics_pl\\csv_url\\{category}\\bad_url.csv'):
            # если файл bad_url.csv существует
            if os.path.isfile(f'c:\\asics_pl\\csv_url\\{category}\\url.csv'):
                # если файл url.csv существует, удаляем его
                os.remove(f'c:\\asics_pl\\csv_url\\{category}\\url.csv')
            # переименовываем bad_url.csv в url.csv
            os.rename(f'c:\\asics_pl\\csv_url\\{category}\\bad_url.csv', f'c:\\asics_pl\\csv_url\\{category}\\url.csv')
            if os.path.isfile(f'c:\\asics_pl\\csv_url\\{category}\\bad_url.csv'):
                # если bad_url.csv все еще существует (например, если произошла ошибка при переименовании)
                # удаляем его
                os.remove(f'c:\\asics_pl\\csv_url\\{category}\\bad_url.csv')
                retry_count += 1
            else:
                break

def main_asio():
    with open(f'c:\\scrap_tutorial-master\\tesla\\url\\url_tesla.csv', newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        counter = 0
        for url in urls:
            counter += 1
            process_url(url[0], counter)
            print(f"ссылка {counter} из {len(urls)}")
            time.sleep(2)


if __name__ == '__main__':
    main_asio()
