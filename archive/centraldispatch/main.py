import re
import glob
import json
import os
from bs4 import BeautifulSoup
import shutil
import pickle
import tempfile
import zipfile
import time
import random
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv


current_directory = os.getcwd()
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, "temp")
list_path = os.path.join(temp_path, "list")
products_path = os.path.join(temp_path, "products")


def creative_folders():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, json_path, html_path]:
        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
        except Exception as e:
            print(f"Ошибка при создании {folder}: {e}")



def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()

    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    # chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    # chrome_options.add_argument('--disable-extensions') # Отключает использование расширений
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
    s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
      '''
    })
    return driver




def get_selenium():
    url = 'https://id.centraldispatch.com/Account/Login?ReturnUrl=%2Fconnect%2Fauthorize%2Fcallback%3Fclient_id%3Dcentraldispatch_authentication%26scope%3Dlisting_service%2520offline_access%2520openid%26response_type%3Dcode%26redirect_uri%3Dhttps%253A%252F%252Fwww.centraldispatch.com%252Fprotected'
    dict_ang = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']

    driver = get_chromedriver()
    driver.maximize_window()
    driver.get(url)
    wait = WebDriverWait(driver, 60)
    time.sleep(1)
    wait_email = wait.until(
        EC.presence_of_element_located((By.XPATH, '//input[@id="Username"]')))
    email = driver.find_element(By.XPATH, '//input[@id="Username"]')
    email.send_keys('ospro1')
    passwords = driver.find_element(By.XPATH, '//input[@id="password"]')
    passwords.send_keys('LggtTLQC123!')
    passwords.send_keys(Keys.RETURN)

    for i in dict_ang[1:2]:
        for j in range(1, 2):
            driver.refresh()
            url_search = f'https://app.centraldispatch.com/company-search?s={i}&page={j}&size=100&sort=relevance&desc=true'
            driver.get(url_search)
            time.sleep(20)
            with open(f"c:\\DATA\\centraldispatch\\list\\{i}_{j}.html", "w", encoding='utf-8') as file:
                file.write(driver.page_source)



def parsing_list():
    with open('url_products.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        file = f"C:\\DATA\\centraldispatch\\list\\*.html"
        files_html = glob.glob(file)
        for item in files_html:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            table = soup.find('tbody', attrs={'class': 'cd-company-search-MuiTableBody-root'})
            companys = table.find_all('tr')
            urls = []
            for i in companys:
                url_company = i.find('td').find('a').get('href').replace("https://app.centraldispatch.com/ratings/overview?customerid=", "https://www.centraldispatch.com/protected/rating/client-snapshot?id=")
                writer.writerow([url_company])
                # urls.append(url_company)
            # print(urls[0])
def parsing_products():
    with open('products.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        file = f"C:\\DATA\\centraldispatch\\products\\*.html"
        files_html = glob.glob(file)
        for item in files_html:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            try:
                company_information = soup.find_all('div', attrs={'class': 'panel-body'})[0]
            except:
                continue
            contact_information = soup.find_all('div', attrs={'class': 'panel-body'})[1]


            company_name = soup.find('h1', attrs={'style': 'display:inline'}).text.strip()
            company_location  = company_information.find('address').text.replace("\n", " ").strip()
            main_phone = contact_information.find('a', attrs={'id': 'listingPhone'}).text.strip()
            local_phone = contact_information.find('a', attrs={'id': 'localPhone'}).text.strip()
            owner_manager = company_information.find('span', attrs={'id': 'principalContact'}).text.strip()
            contact = contact_information.find('span', attrs={'id': 'contactNames'}).text.strip()
            paragraphs = company_information.find_all('p')
            business_type = ""
            # Проходим по каждому параграфу
            for paragraph in paragraphs:
                # Если в параграфе есть текст 'Business Type:'
                if 'Business Type:' in paragraph.text:
                    # Извлекаем текст после 'Business Type:'
                    business_type = paragraph.text.split('Business Type:')[1].strip()
                    # prin//t(business_type)  # Выведет: Carrier
            # business_type = company_information.find('h1', attrs={'style': 'display:inline'}).text.strip()
            datas = [company_name, business_type, company_location,main_phone, local_phone, owner_manager, contact]
            writer.writerow(datas)





if __name__ == '__main__':
    # creative_folders()
    # get_selenium()
    # parsing()
    parsing_products()
