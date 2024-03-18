from datetime import datetime
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
import mysql.connector

conn = mysql.connector.connect(
    host="88.99.217.197",  # Адрес хоста базы данных
    user="aiorg_ai",  # Имя пользователя базы данных
    password="y;*?[86fqWmZ",  # Пароль пользователя базы данных
    database="aiorg_ai"  # Имя базы данных
)


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
    folder = r'C:\scrap_tutorial-master\amazon\url\*.csv'
    files_html = glob.glob(folder)
    for item in files_html:
        with open(item, newline='', encoding='utf-8') as files:
            urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
            count = 0
            for url in urls[:1]:
                """Настройка прокси серверов случайных"""
                proxy = random.choice(proxies)
                proxy_host = proxy[0]
                proxy_port = proxy[1]
                proxy_user = proxy[2]
                proxy_pass = proxy[3]

                proxi = {
                    'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
                    'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
                }
                count += 1

                new_url = new_url = re.sub(r'(https://www.amazon.com).*(/dp/\d+).*', r'\1\2', url[0])
                new_url = new_url + "?&tag=ebooks0d4-20"
                # print(new_url)
                response = requests.get(url[0],
                                        headers=headers, cookies=cookies, proxies=proxi)

                src = response.text
                soup = BeautifulSoup(src, 'lxml')
                productTitle = soup.find('span', attrs={'id': 'productTitle'}).text.strip()
                img_canvas = soup.find('div', attrs={'id': 'imageBlockOuter'})
                regex_all_image = re.compile('a-column a-span3 a-spacing-micro imageThu.*')
                images = img_canvas.find_all('img')
                image_urls = []
                for i in images:
                    url_jpg = i.get('src')
                    new_url_jpg = re.sub(r'\._AC_.*\.jpg|_SX.*\.jpg', '.jpg', url_jpg)
                    image_urls.append(new_url_jpg)

                app_prices = soup.find('div', attrs={'id': 'tmmSwatches'})
                prices = []
                for span in app_prices.find_all('span', class_=["a-color-base",
                                                                "a-color-secondary"]):  # Поиск нескольких класов
                    price_text = span.get_text(strip=True)
                    price = price_text.replace('$', '').replace("from ", "").strip()
                    prices.append(price)

                prices_dict = {price: 1 for price in prices}
                # преобразуем словарь обратно в список
                prices = list(prices_dict.keys())
                product_details = []
                detail_list = soup.find('ul', class_='detail-bullet-list')
                for li in detail_list.find_all('li'):
                    item = li.text.replace('&rlm;', '').replace('&lrm;', '')
                    item = re.sub(' +', ' ', item)  # remove multiple spaces
                    item = item.replace('\n', '')  # remove newlines
                    item = item.replace('\u200f', '').replace(' \u200e ', ' ')
                    item = item.replace("  : ", "_")
                    item = item.strip()
                    product_details.append(item)
                best_sellers_rank = soup.find('ul', class_='zg_hrsr')
                for li in best_sellers_rank.find_all('li'):
                    item = li.span.text.replace('\u200f', '').strip()
                    product_details.append(item)
                book_description = soup.find('div', attrs={'id': 'editorialReviews_feature_div'}).text.replace("\n", "")
                short_story = str(product_details)
                # print(type(short_story))
                cursor = conn.cursor()

                # Получение последнего id и добавление 1
                select_last_id_query = "SELECT MAX(id) FROM aiorg_ai.dle_post;"
                cursor.execute(select_last_id_query)
                cursor.fetchone()
                # last_id = cursor.fetchone()[0]
                # new_id = last_id + 1 if last_id is not None else 1

                # Получение текущей даты и форматирование
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Значения для вставки
                autor = "E-book"
                date = "E-book"
                short_story = short_story
                full_story = "E-book"
                xfields = "E-book"
                title = productTitle
                descr = book_description
                keywords = "E-book"
                category = "E-book"
                alt_name = "E-book"
                comm_num = 0
                allow_comm = 1
                allow_main = 1
                approve = 1
                fixed = 0
                allow_br = 0
                symbol = ""
                tags = ""
                metatitle = ""

                # SQL-запрос для вставки данных
                insert_query = """
                    INSERT INTO aiorg_ai.dle_post (autor, date, short_story, full_story, xfields, title, descr, keywords, category, alt_name, comm_num, allow_comm, allow_main, approve, fixed, allow_br, symbol, tags, metatitle)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """

                insert_values = (autor, current_date, short_story, full_story, xfields, title, descr, keywords, category, alt_name, comm_num, allow_comm, allow_main, approve, fixed, allow_br, symbol, tags, metatitle)

                cursor.execute(insert_query, insert_values)
                conn.commit()

                conn.close()
               
                # print(productTitle)
                # print(prices)
                # print(image_urls)
                # print(product_details)
                # print(book_description)



if __name__ == '__main__':
    # get_requests()
    parsing()
