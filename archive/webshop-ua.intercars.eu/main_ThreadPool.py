from selenium.webdriver.chrome.service import Service
import os
from pathlib import Path
import shutil
import tempfile
import os
import concurrent.futures
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import zipfile
import time
# import undetected_chromedriver as webdriver
from selenium import webdriver
import undetected_chromedriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv

class ProxyExtension:
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]},
        "minimum_chrome_version": "76.0.0"
    }
    """

    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: %d
            },
            bypassList: ["localhost"]
        }
    };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
        callbackFn,
        { urls: ["<all_urls>"] },
        ['blocking']
    );
    """

    def __init__(self, host, port, user, password):
        self._dir = os.path.normpath(tempfile.mkdtemp())

        manifest_file = os.path.join(self._dir, "manifest.json")
        with open(manifest_file, mode="w") as f:
            f.write(self.manifest_json)

        background_js = self.background_js % (host, port, user, password)
        background_file = os.path.join(self._dir, "background.js")
        with open(background_file, mode="w") as f:
            f.write(background_js)

    @property
    def directory(self):
        return self._dir

    def __del__(self):
        shutil.rmtree(self._dir)

def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    # chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--proxy-server=45.14.174.253:80")
    # chrome_options.add_argument('--ignore-certificate-errors')
    # chrome_options.add_argument('--ignore-ssl-errors')
    # chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument("--disable-cache")  # Отключение кэширования
    chrome_options.add_argument("--disable-cookies")  # Отключение использования куков
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-setuid-sandbox')
    # driver = webdriver.Chrome(options=chrome_options)
    driver = undetected_chromedriver.Chrome(options=chrome_options)

    return driver
def process_row(row):
    name_product = (','.join(row))
    name_product_find = name_product.replace(",", " ")
    name_file = name_product.replace(",", "_")
    file_path = Path('e:/intercars_html') / f'{name_file}.html'
    if file_path.exists():
        return  # Пропускаем файл, если он уже существует
    driver = get_chromedriver()
    driver.get(url=url)

    try:
        find_product_wait = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@class="ui-autocomplete-input"]')))
        find_product = driver.find_element(By.XPATH, '//input[@class="ui-autocomplete-input"]')
        find_product.clear()

        actions = ActionChains(driver)
        actions.move_to_element(find_product).click().send_keys(name_product_find).perform()

        actions = ActionChains(driver)
        actions.move_to_element(find_product).click().send_keys(Keys.RETURN).perform()

        time.sleep(1)
        try:
            driver.find_element(By.XPATH, '//div[contains(text(), "Немає результатів")]')
            # driver.close()
            # driver.quit()
        except:
            button_img_wain = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="art-images margincenter"]')))
            button_img = driver.find_element(By.XPATH, '//div[@class="art-images margincenter"]').click()
            wait_img_full = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="swal2-container"]')))
            time.sleep(1)
            with open(file_path, "w", encoding='utf-8') as file:
                file.write(driver.page_source)
            # time.sleep(1)
            # driver.close()
            # driver.quit()
    except Exception as e:
        save_error_to_csv(name_file)
        print(f"Ошибка в обработке строки: {name_file}")
        print(str(e))
        # driver.close()
        # driver.quit()
    finally:
        driver.close()
        driver.quit()


def save_link_all_product(url):
    with open(f'C:\\scrap_tutorial-master\\webshop-ua.intercars.eu\\csv\\output.csv', newline='',
              encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        
        for start in range(0, len(csv_reader), 100):
            end = start + 100
            batch = csv_reader[start:end]
            counter = 0

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for row in batch:
                    counter += 1
                    print(end)
                    future = executor.submit(process_row, row)
                    futures.append(future)

                concurrent.futures.wait(futures)



def save_error_to_csv(name_file):
    with open('errors.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([name_file])



if __name__ == '__main__':
    url = "https://webshop-ua.intercars.eu/zapchasti/"
    save_link_all_product(url)