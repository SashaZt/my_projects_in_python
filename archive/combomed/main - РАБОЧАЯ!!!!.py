import os
import time
import undetected_chromedriver
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv


def get_undetected_chromedriver():
    # Обход защиты
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--proxy-server=45.14.174.253:80")
    # chrome_options.add_argument('--ignore-certificate-errors')
    # chrome_options.add_argument('--ignore-ssl-errors')
    # chrome_options.add_argument('--disable-extensions')
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-setuid-sandbox')
    # driver = webdriver.Chrome(options=chrome_options)
    driver = undetected_chromedriver.Chrome(options=chrome_options)

    return driver


def process_url(url):
    try:
        name_file = url.split('/')[-1]
        file_name = f"{name_file}.html"
        if os.path.exists(os.path.join('data', file_name)):
            return
        driver = get_undetected_chromedriver()
        driver.maximize_window()
        driver.get(url)
        next_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@class="navbar-brand"]')))
        driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
        # Тестово
        driver.stop_client()
        driver.set_page_load_timeout(1)
        driver.set_script_timeout(1)
        time.sleep(1)
        with open(os.path.join('data', file_name), "w", encoding='utf-8') as fl:
            fl.write(driver.page_source)
    except TimeoutException:
        print(f"Timeout exception occurred while loading {url}")
    finally:
        driver.close()
        driver.quit()


def save_html():
    """Рабочий код"""
    with open('url.csv', newline='', encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        urls = [row[0] for row in csv_reader]
        with ThreadPoolExecutor(max_workers=15) as executor:
            executor.map(process_url, urls)
    """Тестовый после 15 ссылок пауза"""
    # with open('url.csv', newline='', encoding='utf-8') as files:
    #     csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
    #     urls = [row[0] for row in csv_reader]
    #     with ThreadPoolExecutor(max_workers=15) as executor:
    #         count = 0  # переменная для подсчета количества открытых страниц
    #         for url in urls:
    #             if count % 15 == 0 and count != 0:  # если открыто 15 страниц, делаем паузу в 1 минуту
    #                 time.sleep(30)
    #             executor.submit(process_url, url)
    #             count += 1


if __name__ == '__main__':
    save_html()
