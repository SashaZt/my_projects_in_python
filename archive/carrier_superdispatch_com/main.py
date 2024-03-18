from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import csv
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

PROXY_HOST = '37.233.3.100'
PROXY_PORT = 9999
PROXY_USER = 'proxy_alex'
PROXY_PASS = 'DbrnjhbZ88'
# proxies = {
#     'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
#     'https': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
# }
proxies = {"http": f"http://{PROXY_HOST}:{PROXY_PORT}", f"https": f"http://{PROXY_HOST}:{PROXY_PORT}"}
cookies = {
    'companyName': 'NE56%20INC',
    'trackingEnabled': '1',
    'userName': 'Elisha%20DeCaria',
    'userEmail': 'ne56.inc%40gmail.com',
    'userCreatedAt': '1677160795',
    'userHash': '601f79cafc91efb02401475b106adaead34716094bcc3e24d4ac867a060ea3b1',
    'userId': 'b1a0a4c9-ae44-43aa-a637-95997621a89d',
    '__cf_bm': 'B5o8_eoVyp3ld3qjXdVqOn8tJnqSSrTHEgaGxzImdh0-1685963058-0-AbNeTMCRlIR4RmXw3eYPNIv+NPFDfj/vN85QxO23iC1HDP8VwvA6TKu0yX19bRXbOYF/m8tjP3Ff8UgU9ew9S/8=',
    'userToken': 'b1aae9a1be8d491580f08ca0691d3ac2',
    'csrftoken': 'vWFFb6V9um9FyerCcvoE8qv7q3v5yLzE4XjpGWVAtuF7ha3tXlvsJvjVz1MhHSh6',
    'sessionid': '4ptfyti8pnqvnvx5b9tdkuk944hu8p3r',
    '_dd_s': 'logs=1&id=76c0dd55-0a79-40fe-b9cd-ee0a4cbd529f&created=1685963059185&expire=1685963968162&rum=0',
}

headers = {
    'authority': 'carrier.superdispatch.com',
    'accept': '*/*',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'authorization': 'Token b1aae9a1be8d491580f08ca0691d3ac2',
    # 'cookie': 'companyName=NE56%20INC; trackingEnabled=1; userName=Elisha%20DeCaria; userEmail=ne56.inc%40gmail.com; userCreatedAt=1677160795; userHash=601f79cafc91efb02401475b106adaead34716094bcc3e24d4ac867a060ea3b1; userId=b1a0a4c9-ae44-43aa-a637-95997621a89d; __cf_bm=B5o8_eoVyp3ld3qjXdVqOn8tJnqSSrTHEgaGxzImdh0-1685963058-0-AbNeTMCRlIR4RmXw3eYPNIv+NPFDfj/vN85QxO23iC1HDP8VwvA6TKu0yX19bRXbOYF/m8tjP3Ff8UgU9ew9S/8=; userToken=b1aae9a1be8d491580f08ca0691d3ac2; csrftoken=vWFFb6V9um9FyerCcvoE8qv7q3v5yLzE4XjpGWVAtuF7ha3tXlvsJvjVz1MhHSh6; sessionid=4ptfyti8pnqvnvx5b9tdkuk944hu8p3r; _dd_s=logs=1&id=76c0dd55-0a79-40fe-b9cd-ee0a4cbd529f&created=1685963059185&expire=1685963968162&rum=0',
    'dnt': '1',
    'referer': 'https://carrier.superdispatch.com/tms/loads?stage=delivered&drivers=n&order_by=n&terminals=n&dispatchers=n',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}


def get_undetected_chromedriver():
    # Обход защиты
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--proxy-server=45.14.174.253:80")
    # chrome_options.add_argument('--ignore-certificate-errors')
    # chrome_options.add_argument('--ignore-ssl-errors')
    # chrome_options.add_argument('--disable-extensions')
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-setuid-sandbox')
    # driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)

    return driver
def get_requests():
    cookies = {
        'companyName': 'NE56%20INC',
        'trackingEnabled': '1',
        'userName': 'Elisha%20DeCaria',
        'userEmail': 'ne56.inc%40gmail.com',
        'userCreatedAt': '1677160795',
        'userHash': '601f79cafc91efb02401475b106adaead34716094bcc3e24d4ac867a060ea3b1',
        'userId': 'b1a0a4c9-ae44-43aa-a637-95997621a89d',
        'userToken': 'b1aae9a1be8d491580f08ca0691d3ac2',
        'csrftoken': 'vWFFb6V9um9FyerCcvoE8qv7q3v5yLzE4XjpGWVAtuF7ha3tXlvsJvjVz1MhHSh6',
        'sessionid': '4ptfyti8pnqvnvx5b9tdkuk944hu8p3r',
        '__cf_bm': 'ewgH3.g1zj6yEqkRBXVu7sZMI7UskhKtU7o2N4LgICQ-1685964523-0-AfEWpnQW7Wrx1GfvyfHg1sHKFBM4x4UviOkdIcoLtwJX4kha8udpiZZhLPjvzpv/7eV8IaCnzRsX/1xUlRwwysU=',
        '_dd_s': 'logs=1&id=76c0dd55-0a79-40fe-b9cd-ee0a4cbd529f&created=1685963059185&expire=1685965486454&rum=0',
    }

    headers = {
        'authority': 'carrier.superdispatch.com',
        'accept': '*/*',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
        'authorization': 'Token b1aae9a1be8d491580f08ca0691d3ac2',
        # 'cookie': 'companyName=NE56%20INC; trackingEnabled=1; userName=Elisha%20DeCaria; userEmail=ne56.inc%40gmail.com; userCreatedAt=1677160795; userHash=601f79cafc91efb02401475b106adaead34716094bcc3e24d4ac867a060ea3b1; userId=b1a0a4c9-ae44-43aa-a637-95997621a89d; userToken=b1aae9a1be8d491580f08ca0691d3ac2; csrftoken=vWFFb6V9um9FyerCcvoE8qv7q3v5yLzE4XjpGWVAtuF7ha3tXlvsJvjVz1MhHSh6; sessionid=4ptfyti8pnqvnvx5b9tdkuk944hu8p3r; __cf_bm=ewgH3.g1zj6yEqkRBXVu7sZMI7UskhKtU7o2N4LgICQ-1685964523-0-AfEWpnQW7Wrx1GfvyfHg1sHKFBM4x4UviOkdIcoLtwJX4kha8udpiZZhLPjvzpv/7eV8IaCnzRsX/1xUlRwwysU=; _dd_s=logs=1&id=76c0dd55-0a79-40fe-b9cd-ee0a4cbd529f&created=1685963059185&expire=1685965486454&rum=0',
        'dnt': '1',
        'referer': 'https://carrier.superdispatch.com/tms/loads/1c42b171-6405-4221-b73b-70e43d184a99?next=%2Ftms%2Floads%3Fstage%3Ddelivered%26drivers%3Dn%26order_by%3Dn%26terminals%3Dn%26dispatchers%3Dn&stage=delivered',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }

    response = requests.get(
        'https://carrier.superdispatch.com/internal/web/loads/1c42b171-6405-4221-b73b-70e43d184a99/',
        cookies=cookies,
        headers=headers,
    )
    data = response.json()  # Получаем json-объект
    with open(f'test.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)  # Записываем в файл



def get_all_delivered():

    for i in range(1, 169):
        params = {
            'page': f'{i}',
        }

        response = requests.get(
            'https://carrier.superdispatch.com/internal/web/loads/delivered/',
            params=params,
            cookies=cookies,
            headers=headers,
        )
        data = response.json()  # Получаем json-объект
        with open(f'data_{i}.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)  # Записываем в файл
        time.sleep(10)

def get_selenium():
    url = 'https://carrier.superdispatch.com/tms/loads?stage=delivered&drivers=n&order_by=n&terminals=n&dispatchers=n'
    driver = get_undetected_chromedriver()
    driver.maximize_window()
    driver.get(url)
    time.sleep(5)
    wait = WebDriverWait(driver, 60)
    button_input_email = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="email"]')))

    input_email = driver.find_element(By.XPATH, '//input[@type="text"]')
    input_email.send_keys('ne56.inc@gmail.com')
    input_password = driver.find_element(By.XPATH, '//input[@type="password"]')
    input_password.send_keys('Chisinau2023!')
    input_password.send_keys(Keys.RETURN)
    time.sleep(5)
    file_name = f"carrier.html"
    with open(os.path.join('data', file_name), "w", encoding='utf-8') as fl:
        fl.write(driver.page_source)
    file = f"data/carrier.html"
    with open(file, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    pagin = soup.find('div', attrs={'aria-label': 'Pagination Navigation'}).find_all('span', attrs={
        'class': 'MuiIconButton-label'})[-2:]
    number = int(pagin[0].get_text())
    print(number)

if __name__ == '__main__':
    # get_selenium()
    get_all_delivered()
    # get_requests()
    # get_cloudscraper()

