import os
import csv
import traceback
import concurrent.futures
import re
import time
import psutil
import requests
import undetected_chromedriver
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait
def get_undetected_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument('--headless')
    """Проба"""
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-setuid-sandbox")

    driver = undetected_chromedriver.Chrome()
    return driver
def process_product_row(row):
    bad_product= []
    name_product = (','.join(row))
    name_product_find = name_product.replace(",", " ")
    name_file = name_product.replace(",", "_")
    driver = get_undetected_chromedriver()
    driver.get(url=url)
    driver.maximize_window()
    try:
        find_product_wait = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@class="ui-autocomplete-input"]')))
        find_product = driver.find_element(By.XPATH, '//input[@class="ui-autocomplete-input"]')
        find_product.send_keys(name_product_find)
        find_product.send_keys(Keys.RETURN)
        time.sleep(1)
        try:
            driver.find_element(By.XPATH, '//div[contains(text(), "Немає результатів")]')
            driver.close()
            driver.quit()
        except:
            button_img_wain = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="art-images margincenter"]')))
            button_img = driver.find_element(By.XPATH, '//div[@class="art-images margincenter"]')
            button_img.click()
            wait_img_full = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="swal2-container"]')))
            with open(f"c:\\intercars_html\\{name_file}.html", "w",
                      encoding='utf-8') as file:
                file.write(driver.page_source)
            time.sleep(5)
            driver.close()
            driver.quit()
    except Exception as e:
        bad_product.append(name_product_find)
        with open(f'C:\\webshop-ua.intercars.eu\\csv\\bad_product.csv', 'a', newline='',
                  encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter='\n', quotechar='|')
            writer.writerow(bad_product)
        traceback.print_exc()
        driver.close()
        driver.quit()

def save_link_all_product(url, num_threads=4):
    with open(f'C:\\webshop-ua.intercars.eu\\csv\\output.csv', newline='',
              encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        count_url = 0
        bad_product = []
        counter = 274870
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            for row in csv_reader[274870:]:
                counter += 1
                name_product = (','.join(row))
                name_product_find = name_product.replace(",", " ")
                name_file = name_product.replace(",", "_")
                if os.path.isfile(f"path/to/folder/{name_file}.html"):
                    continue
                else:
                    executor.submit(process_product_row, row)



                #Рабочее
                # executor.submit(process_product_row, row)

if __name__ == '__main__':
    url = "https://webshop-ua.intercars.eu/zapchasti/"
    num_threads = 5 # здесь можно указать количество потоков
    save_link_all_product(url, num_threads=num_threads)
