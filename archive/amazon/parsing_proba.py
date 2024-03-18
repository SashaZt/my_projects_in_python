def main():
    pass


if __name__ == '__main__':
    main()
from bs4 import BeautifulSoup
import csv
import glob
import re
import requests
import json
import cloudscraper
import os
import random
import time
import shutil
import tempfile
from proxi import proxies
from headers_cookies import cookies, headers
import csv


def get_requests():
    with open(f'C:\\scrap_tutorial-master\\amazon\\category.csv', newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        for url in urls:
            proxy = random.choice(proxies)
            proxy_host = proxy[0]
            proxy_port = proxy[1]
            proxy_user = proxy[2]
            proxy_pass = proxy[3]

            proxi = {
                'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
                'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
            }
            response = requests.get(url[0], cookies=cookies, headers=headers, proxies=proxi)
            src = response.text
            soup = BeautifulSoup(src, 'lxml')
            category = soup.find('span', attrs={'class': 'a-size-base a-color-base a-text-bold'}).text

            last_page = int(soup.find('span', attrs={'class': 's-pagination-item s-pagination-disabled'}).text)
            print(last_page)
            next_page = 'https://www.amazon.com' + soup.find('a', attrs={'aria-label': 'Go to page 2'}).get('href')
            with open(f'C:\\scrap_tutorial-master\\amazon\\url\\{category}.csv', 'w', newline='',
                      encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                for i in range(1, last_page + 1):
                    if i == 1:
                        response = requests.get(
                            url[0],
                            cookies=cookies,
                            headers=headers,
                        )
                        soup = BeautifulSoup(response.text, 'lxml')
                        url_products = soup.find_all('a', attrs={'class': 'a-link-normal s-no-outline'})
                        for k in url_products:
                            url_product = 'https://www.amazon.com' + k.get("href")
                            writer.writerow([url_product])
                    if i > 1:
                        response = requests.get(
                            next_page,
                            cookies=cookies,
                            headers=headers,
                        )
                        soup = BeautifulSoup(response.text, 'lxml')
                        next_page_element = soup.find('a', attrs={'aria-label': f'Go to page {i + 1}'})
                        url_products = soup.find_all('a', attrs={'class': 'a-link-normal s-no-outline'})
                        for k in url_products:
                            url_product = 'https://www.amazon.com' + k.get("href")
                            writer.writerow([url_product])

                        # Проверяем, есть ли ссылка на следующую страницу
                        if next_page_element is not None:
                            next_page = 'https://www.amazon.com' + next_page_element.get('href')
                        else:
                            break  # выходим из цикла, если нет ссылки на следующую страницу
                    print(next_page)
                # time.sleep(1)
                # writer.writerow([url_product])


def parsing():
    with open('amazon.html', encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    book_description = soup.find('div', attrs={'id': 'editorialReviews_feature_div'}).text.replace("\n", "")
    print(book_description)



if __name__ == '__main__':
    # get_requests()
    parsing()
