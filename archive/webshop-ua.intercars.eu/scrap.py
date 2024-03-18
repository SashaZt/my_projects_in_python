from selenium.webdriver.chrome.service import Service
import os
from pathlib import Path
import random
import shutil
import tempfile
import os
from proxi import proxies
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

def get_chromedriver(proxy):
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
    proxy_extension = ProxyExtension(*proxy)
    chrome_options.add_argument(f"--load-extension={proxy_extension.directory}")
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
def prepare_data(row):
    # name_product =
    name_product_find = f"{row[1]} {row[0]}"
    name_file = name_product_find.replace(" ", "_")
    """Изменить на e:/intercars_html"""
    file_path = Path('c:/intercars_html') / f'{name_file}.html'
    if file_path.exists():
        return None  # Пропускаем файл, если он уже существует
    else:
        proxy = random.choice(proxies)
        return name_product_find, name_file, proxy
def process_row(data):
    if data is None:
        return
    name_product_find, name_file, proxy = data
    """Изменить на e:/intercars_html"""
    file_path = Path('c:/intercars_html') / f'{name_file}.html'
    driver = get_chromedriver(proxy)
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

        except:
            button_img_wain = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="art-images margincenter"]')))
            button_img = driver.find_element(By.XPATH, '//div[@class="art-images margincenter"]').click()
            wait_img_full = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="swal2-container"]')))
            time.sleep(1)
            name_brand_find = name_product_find.split(' ')[0]
            brand_product = driver.find_element(By.XPATH, '//span[@id="manufacture_30"]').text
            if name_brand_find == brand_product:
                with open(file_path, "w", encoding='utf-8') as file:
                    file.write(driver.page_source)
            # Открываем (или создаем) CSV-файл для записи
                with open('logs_compliance.csv', 'a', newline='') as csvfile:
                    logwriter = csv.writer(csvfile, delimiter=';')
                    logwriter.writerow([file_path, name_product_find])


    except Exception as e:
        save_error_to_csv(name_file)

    finally:
        driver.close()
        driver.quit()


def save_link_all_product(url):
    with open(f'C:\\scrap_tutorial-master\\webshop-ua.intercars.eu\\csv\\output.csv', newline='',
              encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=';', quotechar='|'))

        for start in range(0, len(csv_reader), 10):
            end = start + 10
            batch = csv_reader[start:end]
            counter = 0

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                futures = []
                for row in batch:
                    counter += 1
                    with open('log.txt', 'a') as f:
                        print(end, file=f)
                    data = prepare_data(row)
                    future = executor.submit(process_row, data)
                    futures.append(future)

                concurrent.futures.wait(futures)



def save_error_to_csv(name_file):
    with open('errors.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([name_file])
        print(f'Записано {name_file}')



if __name__ == '__main__':
    url = "https://webshop-ua.intercars.eu/zapchasti/"
    save_link_all_product(url)