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
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv


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
    # proxy_extension = ProxyExtension(*proxy)
    # chrome_options.add_argument(f"--load-extension={proxy_extension.directory}")
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
    url = 'https://opensea.io/assets?search[query]=star'
    driver = get_chromedriver()
    driver.maximize_window()
    driver.get(url)
    time.sleep(5)
    for k in range(20):
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    file_name = f"data.html"
    with open(os.path.join('data', file_name), "w", encoding='utf-8') as fl:
        fl.write(driver.page_source)

def parsing():
    file = f"data/data.html"
    with open(file, encoding="utf-8") as file:
         src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    script_json = soup.find_all('script', type="application/json")
    data_json = json.loads(script_json[4].string)
    with open("data/output.json", "w", encoding='utf-8') as write_file:
        json.dump(data_json, write_file, ensure_ascii=False, indent=4)
    # print(data_json)
    # all_products = soup.find_all('div', attrs={'class': 'sc-29427738-0 sc-53513746-1 cKdnBO jsgfwk Asset--loaded'})
    # urls_clints = []
    # for i in all_products:
    #     url = f"https://opensea.io{i.find('a').get('href')}"
    #     urls_clints.append(url)
    # driver = get_chromedriver()
    # with open('url_client.csv', 'a', newline='') as csvfile:
    #     writer = csv.writer(csvfile)
    #     for u in urls_clints[:5]:
    #         driver.get(u)
    #         time.sleep(5)
    #         try:
    #             url_client = driver.find_element(By.XPATH, '//div[@class="item--collection-detail"]//a').get_attribute('href')
    #         except:
    #             continue
    #         writer.writerow([url_client])
    #






if __name__ == '__main__':
    # get_requests()
    # get_cloudscraper()
    # get_selenium()
    parsing()
