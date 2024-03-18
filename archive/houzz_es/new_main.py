from bs4 import BeautifulSoup
import csv
import os
import random
import time
import json
import requests
import re
from urllib.parse import urlparse

keywords = ["Commercial", "Residential", "LEED", "Greengaurd", "Phthalates", "Polyvinyl", "PVC"]

headers = {
    'authority': 'www.houzz.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru',
    'cache-control': 'no-cache',
    # 'cookie': 'v=1689232282_acaa195e-8fba-4bc6-b1a0-33a3f5187d6d_fcc234c25c227bc932110f5bf7a3ed90; vct=en-US-CR%2Bao69k8B%2Bao69kSByao69k4R2ao69k4h2ao69k; _csrf=rCFYDoBRDb4YRTwntTUysLd-; jdv=t7WOzUb2vHLZtWVVHSk8XJAeN7ua9zR8UkXoYtRfWRbjhUARyr6uKbLj7Jj5SQXvBLcrdsb3Rw6tTUojfDm1itWv448S; documentWidth=1920; hzd=fc53112f-9ab3-434e-8574-64d8b9bc3303%3A%3A%3A%3A%3AGetStarted; _gid=GA1.2.1009462869.1689232284; _gat=1; _gcl_au=1.1.1320362438.1689232284; _ga_PB0RC2CT7B=GS1.1.1689232284.1.0.1689232284.60.0.0; _ga=GA1.1.836547781.1689232284; _uetsid=7a11f140214c11ee97194fe925ba19d3; _uetvid=7a1226e0214c11ee892f8562f18e84d3; _pin_unauth=dWlkPU9HRmhOalF6T0dRdE9EYzBaUzAwT1RGaExXRXpNR1V0WWprMU5qazFNRGxpWldGaA',
    'dnt': '1',
    'pragma': 'no-cache',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}
file_path = "proxies.txt"


def is_valid_url(url):
    # проверка, является ли ссылка абсолютной и не содержит ли она нежелательных элементов
    parsed = urlparse(url)
    if bool(parsed.netloc) and bool(parsed.scheme):
        if "javascript:void(0)" not in url and "tel:" not in url and "#" not in url:
            return True
    return False


def load_proxies(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if '@' in line and ':' in line]


def get_random_proxy(proxies):
    return random.choice(proxies)


def get_url_company():
    if os.path.exists('url_products.csv'):
        return
    with open('houzz_input.txt', 'r') as file:
        for line in file:
            url = line.strip()

            proxies = load_proxies(file_path)
            proxy_attempt_count = 0
            connected = False
            while not connected and proxy_attempt_count < 1:
                s = requests.Session()
                proxy = get_random_proxy(proxies)
                login_password, ip_port = proxy.split('@')
                login, password = login_password.split(':')
                ip, port = ip_port.split(':')
                proxy_dict = {
                    "http": f"http://{login}:{password}@{ip}:{port}",
                    "https": f"http://{login}:{password}@{ip}:{port}"
                }
                s.proxies = proxy_dict
                for attempt_count in range(3):
                    try:
                        response = s.get(url, headers=headers)
                        connected = True
                        break
                    except:
                        continue
                proxy_attempt_count += 1
                if connected:
                    break
            if not connected:
                continue
            src = response.text
            soup = BeautifulSoup(src, 'lxml')
            script_json = soup.find('script', type="application/json")
            data_json = json.loads(script_json.string)
            try:
                pagination_total = int(
                    data_json['data']['stores']['data']['ViewProfessionalsStore']['data']['paginationSummary'][
                        'total'].replace(',', ''))
            except:
                continue
            amount_page = pagination_total // 15
            coun = 0

            with open('url_products.csv', 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                count = 0
                for i in range(1, amount_page + 2):
                    pause_time = random.randint(1, 5)
                    count += 1
                    datas_urls = []
                    if i == 1:
                        url_first = url
                        proxy_attempt_count = 0
                        connected = False
                        while not connected and proxy_attempt_count < 1:
                            s = requests.Session()
                            proxy = get_random_proxy(proxies)
                            login_password, ip_port = proxy.split('@')
                            login, password = login_password.split(':')
                            ip, port = ip_port.split(':')

                            proxy_dict = {
                                "http": f"http://{login}:{password}@{ip}:{port}",
                                "https": f"http://{login}:{password}@{ip}:{port}"
                            }
                            s.proxies = proxy_dict

                            for attempt_count in range(3):
                                try:
                                    response = s.get(url_first, headers=headers)
                                    connected = True
                                    break
                                except:
                                    continue

                            proxy_attempt_count += 1
                            if connected:
                                break

                        if not connected:
                            continue
                        src_1 = response.text
                        soup = BeautifulSoup(src_1, 'lxml')
                        try:
                            products_urls = soup.find('ul', attrs={'class': 'hz-pro-search-results mb0'}).find_all(
                                'a')
                        except:
                            continue
                        for u in products_urls:
                            url_sc = u.get("href")
                            writer.writerow([url_sc])

                    elif i > 1:
                        coun += 15
                        urls = f'{url}?fi={coun}'
                        proxy_attempt_count = 0
                        connected = False
                        while not connected and proxy_attempt_count < 1:
                            s = requests.Session()
                            proxy = get_random_proxy(proxies)
                            login_password, ip_port = proxy.split('@')
                            login, password = login_password.split(':')
                            ip, port = ip_port.split(':')

                            proxy_dict = {
                                "http": f"http://{login}:{password}@{ip}:{port}",
                                "https": f"http://{login}:{password}@{ip}:{port}"
                            }
                            s.proxies = proxy_dict

                            for attempt_count in range(3):
                                try:
                                    response = s.get(urls, headers=headers)
                                    connected = True
                                    break
                                except:
                                    continue
                            proxy_attempt_count += 1
                            if connected:
                                break

                        if not connected:
                            continue
                        src_2 = response.text
                        soup = BeautifulSoup(src_2, 'lxml')
                        try:
                            products_urls = soup.find('ul', attrs={'class': 'hz-pro-search-results mb0'}).find_all('a')
                        except:
                            continue
                        for u in products_urls:
                            url_pr = u.get("href")
                            writer.writerow([url_pr])


def get_company():
    if os.path.exists('data_test.csv'):
        os.remove('data_test.csv')
    with open(f'data_test.csv', "w", errors='ignore', encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=",", lineterminator="\r", quoting=csv.QUOTE_ALL)
        headers_csv = ('url', 'name_company', 'www_company', 'telephone_company', 'address', 'street_address',
                       'addressLocality', 'addressRegion', 'postalCode', 'addressCountry', 'emails',
                       "Commercial", "Residential", "LEED", "Greengaurd", "Phthalates", "Polyvinyl", "PVC")
        writer.writerow(headers_csv)
        with open('url_products.csv', newline='',
                  encoding='utf-8') as files:
            csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
            coum = 0
            for url in csv_reader[55:57]:
                proxies = load_proxies(file_path)
                proxy_attempt_count = 0
                connected = False
                while not connected and proxy_attempt_count < 1:
                    s = requests.Session()
                    proxy = get_random_proxy(proxies)
                    login_password, ip_port = proxy.split('@')
                    login, password = login_password.split(':')
                    ip, port = ip_port.split(':')

                    proxy_dict = {
                        "http": f"http://{login}:{password}@{ip}:{port}",
                        "https": f"http://{login}:{password}@{ip}:{port}"
                    }
                    s.proxies = proxy_dict

                    for attempt_count in range(3):
                        try:
                            response = s.get(url[0], headers=headers)
                            connected = True
                            break
                        except:
                            continue
                    proxy_attempt_count += 1
                    if connected:
                        break
                if not connected:
                    continue

                emails = set()
                src = response.text
                soup = BeautifulSoup(src, 'lxml')
                script_tag = soup.find('script', {'type': 'application/json'})
                try:
                    json_data = json.loads(script_tag.string)
                except:
                    print(f"{url[0]} -------------------------------- Нет данных")
                try:
                    sfru = json_data['sfru']

                except:
                    sfru = None
                try:
                    name_company = json_data['data']['stores']['data']['MetaDataStore']['data']['htmlMetaTags'][
                        2]['attributes']['content']
                except:
                    name_company = None
                try:
                    telephone_company = \
                        json_data['data']['stores']['data']['ProProfileStore']['data']['user']['professional'][
                            'formattedPhone']
                except:
                    telephone_company = None
                contact_email = ""
                try:
                    www_company = \
                        json_data['data']['stores']['data']['ProProfileStore']['data']['user']['professional'][
                            'rawDomain']
                except:
                    pass
                main_site = requests.get(www_company)
                Commercial = 'no'
                Residential = 'no'
                LEED = 'no'
                Greengaurd = 'no'
                Phthalates = 'no'
                Polyvinyl = 'no'
                PVC = 'no'
                print(url[0])
                print('Идем дальше')
                if main_site is not None:
                    main_soup = BeautifulSoup(main_site.text, 'html.parser')
                    emails |= set(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', main_site.text))
                    main_text = main_soup.get_text().lower()
                    Commercial = 'yes' if 'commercial' in main_text else 'no'
                    Residential = 'yes' if 'residential' in main_text else 'no'
                    LEED = 'yes' if 'leed' in main_text else 'no'
                    Greengaurd = 'yes' if 'greengaurd' in main_text else 'no'
                    Phthalates = 'yes' if 'phthalates' in main_text else 'no'
                    Polyvinyl = 'yes' if 'polyvinyl' in main_text else 'no'
                    PVC = 'yes' if 'pvc' in main_text else 'no'
                    main_links = set([a['href'] for a in main_soup.find_all('a', href=True)])
                    for link in main_links:
                        if not link.startswith('http'):
                            if www_company.endswith('/') and link.startswith('/'):
                                link = www_company + link[1:]
                            else:
                                link = www_company + link
                        if is_valid_url(link):
                            url_link = link
                        attempt_count = 0
                        connected = False
                        print(link)
                        while not connected and attempt_count < 1:
                            try:
                                s = requests.Session()
                                proxy = get_random_proxy(proxies)
                                login_password, ip_port = proxy.split('@')
                                login, password = login_password.split(':')
                                ip, port = ip_port.split(':')

                                proxy_dict = {
                                    "http": f"http://{login}:{password}@{ip}:{port}",
                                    "https": f"http://{login}:{password}@{ip}:{port}"
                                }
                                s.proxies = proxy_dict
                                site = s.get(url_link, headers=headers)
                                connected = True
                            except:
                                attempt_count += 1
                                print(site.status_code)
                                print(url_link)
                        if not connected:
                            continue
                        soup = BeautifulSoup(site.text, 'html.parser')
                        domain = urlparse(www_company).netloc
                        matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', site.text)
                        emails |= set([email for email in matches if
                                       not (email.endswith('.png') or email.endswith('.jpg')) and email.endswith(
                                           domain)])

                        text = soup.get_text().lower()
                        Commercial = 'yes' if 'commercial' in text else Commercial
                        Residential = 'yes' if 'residential' in text else Residential
                        LEED = 'yes' if 'leed' in text else LEED
                        Greengaurd = 'yes' if 'greengaurd' in text else Greengaurd
                        Phthalates = 'yes' if 'phthalates' in text else Phthalates
                        Polyvinyl = 'yes' if 'polyvinyl' in text else Polyvinyl
                        PVC = 'yes' if 'pvc' in text else PVC

                try:
                    address_company = \
                        json_data['data']['stores']['data']['ProProfileStore']['data']['user']['professional'][
                            'formattedAddress']
                except:
                    pass
                address = ''
                try:
                    soup_add = BeautifulSoup(address_company, 'lxml')
                    address_elements = soup_add.find_all('span', itemprop='streetAddress')
                    for element in address_elements:
                        address += element.text.strip() + ' '
                except:
                    pass
                try:
                    postal_code_element = soup_add.find('span', itemprop='postalCode')
                    if postal_code_element:
                        address += postal_code_element.text.strip() + ' '
                except:
                    pass
                try:
                    locality_element = soup_add.find('span', itemprop='addressLocality')
                    if locality_element:
                        address += locality_element.text.strip() + ' '
                except:
                    pass
                street_address = ""
                addressLocality = ""
                addressRegion = ""
                postalCode = ""
                addressCountry = ""
                try:
                    street_add = json_data['data']['stores']['data']['PageStore']['data']['pageDescriptionFooter']
                    soup_s = BeautifulSoup(street_add, 'html.parser')
                    script_tag = soup_s.find('runnable', type='application/ld+json')
                    if script_tag:
                        json_data_script = script_tag.string.strip()
                        data = json.loads(json_data_script)
                        for item_add in data:
                            if 'address' in item_add:
                                try:
                                    street_address = item_add['address'].get('streetAddress')
                                except:
                                    street_address = ""
                                try:
                                    addressLocality = item_add['address'].get('addressLocality')
                                except:
                                    addressLocality = ""
                                try:
                                    addressRegion = item_add['address'].get('addressRegion')
                                except:
                                    addressRegion = ""
                                try:
                                    postalCode = item_add['address'].get('postalCode')
                                except:
                                    postalCode = ""
                                try:
                                    addressCountry = item_add['address'].get('addressCountry')
                                except:
                                    addressCountry = ""
                except:
                    pass
                if not postalCode:
                    postalCode = \
                        json_data['data']['stores']['data']['ProProfileStore']['data']['user']['professional']['zip']
                if not addressLocality:
                    addressLocality = \
                        json_data['data']['stores']['data']['ProProfileStore']['data']['user']['professional']['city']
                if not addressCountry:
                    addressCountry = \
                        json_data['data']['stores']['data']['FooterStore']['data']['footerInfo']['currentCcTld'][
                            'countryNativeName']
                datas = [
                    [sfru, name_company, www_company, telephone_company, address, street_address,
                     addressLocality, addressRegion, postalCode, addressCountry, emails, Commercial, Residential,
                     LEED, Greengaurd, Phthalates, Polyvinyl, PVC]
                ]

                writer.writerows(datas)
                coum += 1
                print(coum)


if __name__ == '__main__':
    get_url_company()
    get_company()
