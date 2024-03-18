import math
import pickle
from bs4 import BeautifulSoup
from pathlib import Path
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import pandas as pd
import re
import os
import csv
import json
import glob
import time


def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
    s = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=chrome_options)
    """Рабочая настройка для обхода Cloudflare """
    return driver

cookies = {
    'noticebar_cookie': '1',
    '_dd_s': 'rum=0&expire=1688404813767',
    'g2g_regional': '%7B%22country%22%3A%22UA%22%2C%22currency%22%3A%22USD%22%2C%22language%22%3A%22en%22%7D',
}


def get_url_category(url):
    folder_path = "c:/Temp/g2g/"
    # folder_path = 'C:/Users/msi/Desktop/g2g/temp/'

    # Получаем список всех .html файлов в папке
    files = glob.glob(folder_path + "*.html")

    # Удаляем каждый файл
    for file in files:
        os.remove(file)
    if os.path.exists('urls.csv'):
        os.remove('urls.csv')

    driver = get_chromedriver()
    driver.get(url)
    driver.maximize_window()
    for cookie_name, cookie_value in cookies.items():
        cookie_dict = {'name': cookie_name, 'value': cookie_value}
        driver.add_cookie(cookie_dict)
    try:
        counter_wait_url = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@class="text-secondary"]')))
    except:
        print('Не загрузилась')
        return
    time.sleep(7)

    about_results = driver.find_element(By.XPATH, '//div[@class="text-secondary"]').text.replace(",", "")
    result_number = int(re.search(r'\d+', about_results).group())
    url_in_page = 48
    list_url = math.ceil(result_number / url_in_page)
    coun = 0
    for i in range(0, list_url + 1):
        if i == 1:
            coun += 1
            name_files = Path(folder_path) / f'data_{coun}.html'
            driver.get(url)
            time.sleep(7)
            driver.execute_script("window.scrollBy(0,1800)", "")
            with open(name_files, "w", encoding='utf-8') as file:
                file.write(driver.page_source)
        elif i > 1:
            coun += 1
            name_files = Path(folder_path) / f'data_{coun}.html'
            driver.get(f'{url}&page={i}')
            time.sleep(7)
            driver.execute_script("window.scrollBy(0,1800)", "")
            with open(name_files, "w", encoding='utf-8') as file:
                file.write(driver.page_source)

    # folders_html = [r"C:\Users\msi\Desktop\g2g\temp\*.html"]
    folders_html = [r"c:\Temp\g2g\*.html"]
    if os.path.exists('urls.csv'):
        os.remove('urls.csv')
    for file in folders_html:
        files_json = glob.glob(file)
        for item in files_json:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            card_product = soup.find('div', attrs={'class': 'row q-col-gutter-sm-md q-px-sm-md'}).find_all('div', attrs={'class': 'full-height full-width position-relative'})
            for i in card_product:
                href = i.find("a").get('href')
                with open('urls.csv', 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([href])  # добавление URL в csv

    print(f'Всего {about_results}')
    driver.close()
    driver.quit()

def get_url_product(url):
    if os.path.exists('data.csv'):
        os.remove('data.csv')
    with open('urls.csv', newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        driver = get_chromedriver()
        driver.get(url)
        for cookie_name, cookie_value in cookies.items():
            cookie_dict = {'name': cookie_name, 'value': cookie_value}
            driver.add_cookie(cookie_dict)
        driver.refresh()
        cout = 0
        for url in urls:
            products_all = []
            driver.get(url[0])
            cout +=1

            # time.sleep(1)
            try:
                counter_wait_url = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@class="precheckout__title precheckout__offer-title"]')))
            except:
                print(f'ошибка на странице, мы ее пропустили и идем дальше {url[0]}')
                continue
            try:
                if driver.find_element(By.XPATH, '//div[@class="precheckout__title precheckout__offer-title"]'):
                    counter_wait_url = WebDriverWait(driver, 60).until(
                        EC.element_to_be_clickable((By.XPATH, '//div[@class="precheckout__title precheckout__offer-title"]')))
                    try:
                        name_server = driver.find_element(By.XPATH,
                                                          '//div[@class="precheckout__title precheckout__offer-title"]').text
                    except:
                        name_server = ""

                    try:
                        server_regions = driver.find_elements(By.XPATH,
                                                              '//div[@class="pi-container"]//div[@class=" text-weight-medium"]')
                    except:
                        server_regions = ""
                    try:
                        sr = driver.find_elements(By.XPATH,
                                                  '//div[@class="seller_details-region-main"]//div[@class="region_left-detail"]')
                    except:
                        sr = ''

                    price_server = driver.find_element(By.XPATH,
                                                       '//span[@id="displayPrice"]').text.replace(
                        ".", ",")
                    try:
                        server_region = driver.find_element(By.XPATH,
                                                       '//div[@class="pi-container"]//div[@class=" text-weight-medium"]').text
                    except:
                        server_region = None

                    try:
                        unit_price = driver.find_element(By.XPATH, '//span[@id="precheckout_ppu_amount"]').text.replace(
                            ".", ",")
                    except:
                        unit_price = None

                    try:
                        server_Platform = server_regions[2].text
                    except:
                        server_Platform = None
                    try:
                        server_ServiceType = server_regions[1].text
                    except:
                        server_ServiceType = None
                    try:
                        stock = driver.find_element(By.XPATH, '//input[@class="stock-box__count"]').get_attribute('value')
                    except:
                        stock = ""
                    try:
                        checkout_devlivery = driver.find_element(By.XPATH,'//div[@class="available-section"]//div').text
                    except:
                        checkout_devlivery = ""
                    products_all.append(
                            {
                                'price': price_server,
                                'unit_price': unit_price,
                                'name': name_server,
                                'region': server_region,
                                'Platform': server_Platform,
                                'ServiceType': server_ServiceType,
                                'Stock': stock,
                                'checkout_devlivery': checkout_devlivery

                            }
                        )
            except:
                continue

            # Создание DataFrame и запись в файл на каждой итерации
            df = pd.DataFrame(products_all)
            # Проверяем, существует ли файл
            if os.path.isfile("data.csv"):
                # Если файл существует, не записываем заголовок
                df.to_csv("data.csv", mode='a', header=False, index=False, sep=';')
            else:
                # Если файла нет, записываем заголовок
                df.to_csv("data.csv", mode='w', header=True, index=False, sep=';')

        print('Все сделал')
        driver.close()
        driver.quit()



def parse_content():
    print("Вставьте ссылку")
    # url = input()
    url = 'https://www.g2g.com/categories/wow-boosting-service?seller=AMELIBOOST'
    get_url_category(url)
    get_url_product(url)


if __name__ == '__main__':
    parse_content()
