import threading
import mysql.connector
import requests
from bs4 import BeautifulSoup
import re
import time
from concurrent.futures import ThreadPoolExecutor
from proxi import proxies
import concurrent.futures
from config import db_config, use_bd, use_table

cookies = {
    'PHPSESSID_MIKE': 't73notsemv17bsdniokuocsqh1',
    'ActiveBasket': '1',
    'dv_consent': '{"accepted":[{"uid":"1"},{"uid":"6"}],"ts":1704032486}',
}

headers = {
    'authority': 'mike.larsson.pl',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'PHPSESSID_MIKE=t73notsemv17bsdniokuocsqh1; ActiveBasket=1; dv_consent={"accepted":[{"uid":"1"},{"uid":"6"}],"ts":1704032486}',
    'dnt': '1',
    'pragma': 'no-cache',
    'referer': 'https://www.larsson.pl/',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-site',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}


api_key = 'a818a4bc04f177c7ae82bb950ccf95ac'
url = 'https://exist.ru/Price/?pid=6D6023C3'


# Допустим, db_config, cookies, headers уже определены

# def fetch_data(url, proxy, delay=1):
def fetch_data(url, timeout=15):
    # proxy_host, proxy_port, proxy_user, proxy_pass = proxy
    # time.sleep(delay)
    # proxi = {
    #     'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
    #     'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
    # }
    try:
        # response = requests.get(f'http://api.scraperapi.com?api_key={api_key}&url={url}')

        response = requests.get(url, cookies=cookies, headers=headers)
        return response.text
    except requests.RequestException as e:
        print(f"Ошибка запроса: {e} {url}")
        return None


def process_data(url, record_id):
    # def process_data(url, proxy, record_id):
    # data = fetch_data(url, proxy)
    data = fetch_data(url)
    if data is None:
        return None, record_id
    soup = BeautifulSoup(data, 'lxml')
    all_kod = []
    table_category = soup.find('div', attrs={'id': 'cat-con'})
    regex_cart = re.compile('cat-item.*')
    cart_table = table_category.find_all('div', attrs={'class': regex_cart}) if table_category else None

    if not cart_table:
        print(f'Ошибка: Таблица категорий не найдена для URL: {url} id {record_id}')
        return None, record_id  # Возвращаем None в качестве признака отсутствия данных

    urls_category = [u.find('a').get('href') for u in cart_table if u.find('a')]
    for urls in urls_category:
        category_data = fetch_data(urls)  # Используйте переменную `urls`, а не `url`

        if category_data:
            soup_category = BeautifulSoup(category_data, 'lxml')
            table_cods = soup_category.find_all('div', attrs={'class': 'gal_elem kombi'})
            for k in table_cods:
                kod_text = k.find('div', attrs={'class': 'gal_artnr'}).get_text(strip=True)
                match = re.search(r'Nr kat\.: ([\d.]+)', kod_text)
                if match:
                    kod_number = match.group(1).replace('.', '')
                    all_kod.append(kod_number)

    kod_string = ', '.join(all_kod)
    return kod_string, record_id


def update_database(record_id, kod_string):
    if kod_string is None:
        return
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    try:
        update_query = "UPDATE larsson SET Kod_części_zamiennej = %s WHERE id = %s"
        cursor.execute(update_query, (kod_string, record_id))
        cnx.commit()
    except mysql.connector.Error as err:
        print("Ошибка базы данных:", err)
    finally:
        if cnx.is_connected():
            cnx.close()


def get_proxy():
    with threading.Lock():
        proxy = proxies.pop(0)
        proxies.append(proxy)
    return proxy


def get_urls_from_db():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    try:
        cursor.execute(
            "SELECT Model, Url_zapasowa, Kod_części_zamiennej, id FROM larsson WHERE Kod_części_zamiennej IS NULL OR Kod_części_zamiennej = '';")
        url_id_map = {row[1]: row[3] for row in cursor}  # Используйте Url_zapasowa как ключ и id как значение
        return url_id_map
    finally:
        if cnx.is_connected():
            cnx.close()


def main():
    url_id_map = get_urls_from_db()
    with ThreadPoolExecutor(max_workers=1) as executor:
        # future_to_data = {executor.submit(process_data, url, get_proxy(), id): (url, id) for url, id in url_id_map.items()}
        future_to_data = {executor.submit(process_data, url, id): (url, id) for url, id in url_id_map.items()}
        for future in concurrent.futures.as_completed(future_to_data):
            url, record_id = future_to_data[future]
            try:
                data, _ = future.result()
                update_database(record_id, data)
            except Exception as exc:
                print(f'URL {url} (ID {record_id}) generated an exception: {exc}')


if __name__ == "__main__":
    while True:
        main()