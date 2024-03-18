from bs4 import BeautifulSoup
import csv
import requests
import glob
import re
import requests
import json
import cloudscraper
import os
import time
import undetected_chromedriver as webdriver
from selenium.common.exceptions import TimeoutException
# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv

from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor

def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--auto-open-devtools-for-tabs=devtools://devtools/bundled/inspector.html')

    s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=chrome_options)

    return driver

def selenium_get_curl():
    url = 'https://clarity-project.info/tenderer/40109091'
    driver = get_chromedriver()
    driver.get(url)
    time.sleep(10)
    filename = f"amazon.html"
    with open(filename, "w", encoding='utf-8') as fl:
        fl.write(driver.page_source)

def get_requests(all_contacts):
    cookies = {
        'PHPSESSID': 'qm5lcf5b95rqhj66peku0gfdds',
        'stats-mode': '',
        '_ga': 'GA1.1.1717072367.1695057288',
        'cf_clearance': 'KAqZjVy0i0Cqz9XW3o5qP9UFAN8YdbiazRfnSjfGJ_c-1695058899-0-1-f63017bc.c9d121e9.a131485c-0.2.1695058899',
        '__gads': 'ID=09514f638f71cbf5-2281d624e9e30037:T=1695057288:RT=1695058899:S=ALNI_Mbdu4_lrNLBndauaCxWtUuM2Mb5eA',
        '__gpi': 'UID=00000d93b01e6623:T=1695057288:RT=1695058899:S=ALNI_MbzSUYh9iRicV0jmPOW2oG-3pAvYA',
        'clrt_id': '99f92140d6e25890b98991b2de592b7e',
        '_ga_RLEGKLKQPK': 'GS1.1.1695057287.1.1.1695058899.0.0.0',
    }

    headers = {
        'authority': 'clarity-project.info',
        'accept': 'text/html, */*; q=0.01',
        'accept-language': 'ru',
        # 'cookie': 'PHPSESSID=qm5lcf5b95rqhj66peku0gfdds; stats-mode=; _ga=GA1.1.1717072367.1695057288; cf_clearance=KAqZjVy0i0Cqz9XW3o5qP9UFAN8YdbiazRfnSjfGJ_c-1695058899-0-1-f63017bc.c9d121e9.a131485c-0.2.1695058899; __gads=ID=09514f638f71cbf5-2281d624e9e30037:T=1695057288:RT=1695058899:S=ALNI_Mbdu4_lrNLBndauaCxWtUuM2Mb5eA; __gpi=UID=00000d93b01e6623:T=1695057288:RT=1695058899:S=ALNI_MbzSUYh9iRicV0jmPOW2oG-3pAvYA; clrt_id=99f92140d6e25890b98991b2de592b7e; _ga_RLEGKLKQPK=GS1.1.1695057287.1.1.1695058899.0.0.0',
        'dnt': '1',
        'referer': 'https://clarity-project.info/tenderer/40109091',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    for a in all_contacts:
        filename = f"c:\\DATA\\clarity_project_info\\{a}.html"
        if not os.path.exists(filename):
            proxi = {
                'http': 'http://stas9793550:EYG5WlbP@212.86.111.208:2831',
                'https': 'http://stas9793550:EYG5WlbP@212.86.111.208:2831'
            }
            response = requests.get(f'https://clarity-project.info/entity/{a}', cookies=cookies, headers=headers, proxies=proxi)
            time.sleep(10)
            src = response.text
            # json_data = response.json()
            # with open(f'test.json', 'w', encoding='utf-8') as f:
            #     json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл

            with open(filename, "w", encoding='utf-8') as file:
                file.write(src)
            print(f'Сохранил {a}')



def parsing():
    all_contacts = []
    file = "amazon.html"
    with open(file, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    table = soup.find('table', attrs={'class': 'awards-list entity-list sortable table w-100'}).find('tbody').find_all('tr')
    for i in table:
        contact = i.find('td').find('a').get('href').replace('/entity/', '')
        all_contacts.append(contact)
    return all_contacts


def parse_html():
    folder = r'c:\DATA\clarity_project_info\*.html'
    files_html = glob.glob(folder)
    with open('output.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        for item in files_html[:10]:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            edr = soup.find('div', {'class': 'edr'}).text.strip()
            name = soup.find('div', {'class': 'name'}).text.strip()
            contracts_stat_div = soup.find('div', {'class': 'contracts-stat'})
            contracts_stat = ' '.join(contracts_stat_div.stripped_strings)
            contracts_stat_cleaned = ' '.join(contracts_stat.split()).replace('/', ' ')

            addr = soup.find('div', {'class': 'addr'}).text.strip()
            contact_div = soup.find('div', {'class': 'contact'})
            contact = ' '.join(contact_div.stripped_strings)
            contact_cleaned =  ' '.join(contact.split()).replace('/', ' ')
            match = re.match(r'([\w\s\'\-]+)\s+([\w\.\-\_]+@[\w\.\-\_]+)\s+(.+)', contact_cleaned)
            name, email, phone = None, None,None
            if match:
                name, email, phone = match.groups()
            values = [edr, name, contracts_stat_cleaned, addr, name, email, phone]
            writer.writerow(values)


if __name__ == '__main__':
    # selenium_get_curl()
    # all_contacts = parsing()  # Changed to call parsing() and store its result in all_contacts
    # get_requests(all_contacts)
    parse_html()