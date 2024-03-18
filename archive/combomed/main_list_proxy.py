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
from selenium.webdriver.chrome.service import Service
"""ТЕСТ. Если все будет хорошо можно отправлять на парсинг"""
#
#
# def get_undetected_chromedriver():
#     # Обход защиты
#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_argument(
#         '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
#
#     chrome_options.add_argument('--disable-blink-features=AutomationControlled')
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--start-maximized")
#     # chrome_options.add_argument('--headless')
#     """Проба"""
#     #chrome_options.add_argument("--disable-dev-shm-usage")
#     #chrome_options.add_argument("--disable-setuid-sandbox")
#     chrome_options.add_argument('--proxy-server=37.233.3.100:9999')
#
#
#     driver = undetected_chromedriver.Chrome()
#
#     return driver


# Список прокси-серверов
proxies = []

with open('proxylist.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        proxies.append(f"{row[0]}")

# Индекс текущего прокси-сервера
current_proxy_index = 0


def get_undetected_chromedriver():
    global current_proxy_index

    # Выбираем следующий прокси-сервер
    current_proxy = proxies[current_proxy_index]
    # Обход защиты прокси proxy сервер Selenium Селениум
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--proxy-server=%s' % current_proxy)
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')

    driver = webdriver.Chrome(options=chrome_options)
    # Увеличиваем индекс для следующего вызова
    current_proxy_index = (current_proxy_index + 1) % len(proxies)

    return driver

#
# def get_chromedriver():
#     global current_proxy_index
#
#     # Выбираем следующий прокси-сервер
#     current_proxy = proxies[current_proxy_index]
#
#     # Создаем объект chrome_options и добавляем настройки
#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_argument('--proxy-server=%s' % current_proxy)
#     chrome_options.add_argument("--start-maximized")
#     chrome_options.add_argument(
#         '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
#
#     chrome_options.add_argument('--disable-blink-features=AutomationControlled')
#     chrome_options.add_argument("--disable-gpu")
#
#     # Создаем объект webdriver.Chrome
#     s = Service(
#         executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
#     )
#     driver = webdriver.Chrome(
#         service=s,
#         options=chrome_options
#     )
#
#     # Увеличиваем индекс для следующего вызова
#     current_proxy_index = (current_proxy_index + 1) % len(proxies)
#
#     return driver



def process_url(url):
    try:
        name_file = url.split('/')[-1]
        file_name = f"{name_file}.html"
        if os.path.exists(os.path.join('data', file_name)):
            return
        driver = get_undetected_chromedriver()
        driver.maximize_window()
        driver.get("https://2ip.ua/ru/")
        next_button = WebDriverWait(driver, 10).until(
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
    with open('url.csv', newline='', encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        urls = [row[0] for row in csv_reader]
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(process_url, urls)


if __name__ == '__main__':
    save_html()