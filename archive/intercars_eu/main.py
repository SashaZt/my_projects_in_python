from bs4 import BeautifulSoup
import glob
import re
import os
import shutil
import tempfile
import zipfile
import time
import random
import random
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv
from selenium.webdriver.common.keys import Keys


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

    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    # chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument('--headless')
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


def get_chromedriver_parsing():
    chrome_options = webdriver.ChromeOptions()

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-extensions')  # Отключает использование расширений
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=chrome_options)
    return driver


def get_category():
    cookies = {
        'BTID': '4C54089E-29F3-4B81-9FFE-47F1678DF42D',
        'JSESSIONID': 'Y22-747f3ca0-b336-4efe-acdc-f3540d172c43.app22',
    }
    url = 'https://ua.e-cat.intercars.eu/ru/'
    driver = get_chromedriver()
    driver.get(url)
    driver.maximize_window()
    # for cookie_name, cookie_value in cookies.items():
    #     cookie_dict = {'name': cookie_name, 'value': cookie_value}
    #     driver.add_cookie(cookie_dict)
    # time.sleep(1)
    # driver.refresh()
    # # for cookie_name, cookie_value in cookies.items():
    # #     cookie_dict = {'name': cookie_name, 'value': cookie_value}
    # #     driver.add_cookie(cookie_dict)
    # time.sleep(10)

    try:
        wait = WebDriverWait(driver, 60)
        wait_email = wait.until(
            EC.presence_of_element_located((By.XPATH, '//input[@id="loginForm:username"]')))
        email = driver.find_element(By.XPATH, '//input[@id="loginForm:username"]')
        email.send_keys('logisticamotoprox@gmail.com')
        passwords = driver.find_element(By.XPATH, '//input[@id="loginForm:password"]')
        passwords.send_keys('GEkz54x!')
        passwords.send_keys(Keys.RETURN)
        time.sleep(10)
        driver.get('https://ua.e-cat.intercars.eu/ru/motorcycles')
        time.sleep(10)
        urls = driver.find_elements(By.XPATH,
                                    '//div[@class="yCmsContentSlot"]//div[@class="yCmsComponent categorytiles__item"]//a')
        with open('url_category.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for u in urls:
                category = u.get_attribute("href")
                writer.writerow([category])

        # file_name = f"motorcycles.html"
        # with open(file_name, "w", encoding='utf-8') as fl:
        #     fl.write(driver.page_source)
    except Exception as e:
        print(e)
    finally:
        driver.close()
        driver.quit()


def get_product():
    url_start = 'https://ua.e-cat.intercars.eu/ru/'
    driver = get_chromedriver()
    driver.get(url_start)
    driver.maximize_window()
    wait = WebDriverWait(driver, 60)
    wait_email = wait.until(
        EC.presence_of_element_located((By.XPATH, '//input[@id="loginForm:username"]')))
    email = driver.find_element(By.XPATH, '//input[@id="loginForm:username"]')
    email.send_keys('logisticamotoprox@gmail.com')
    passwords = driver.find_element(By.XPATH, '//input[@id="loginForm:password"]')
    passwords.send_keys('GEkz54x!')
    passwords.send_keys(Keys.RETURN)
    url_catalog = 'https://ua.e-cat.intercars.eu/ru/vehicle/full-offer'
    driver.get(url_catalog)
    time.sleep(2)
    # file_name = f"amazon.html"
    # with open(file_name, "w", encoding='utf-8') as fl:
    #     fl.write(driver.page_source)
    if os.path.exists('data.csv'):
        os.remove('data.csv')
    with open(f'C:\\scrap_tutorial-master\\intercars_eu\\price.csv', newline='', encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=';', quotechar='|'))

        for start in csv_reader[0:5]:
            value = start[0]  # Значение из второго столбца

            wait_input = wait.until(
                EC.presence_of_element_located((By.XPATH, '//input[@name="query"]')))
            input_art = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="query"]')))
            # input_art.clear()
            # input_art = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="query"]')))
            input_art.send_keys(Keys.CONTROL + 'a')  # выделить всё
            input_art.send_keys(Keys.DELETE)  # удалить выделенное

            time.sleep(1)
            # input_art = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="query"]')))
            input_art.send_keys(value)
            print(f"{value} с прайса")
            # input_art = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="query"]')))
            button_find = driver.find_element(By.XPATH, '//div[@class="header__searchbuttonsubmit js-search-button-submit js-clk-search-button-trigger"]').click()
            # input_art.send_keys(Keys.RETURN)
            time.sleep(1)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table_products = soup.find('table', attrs={'class': 'listingcollapsed__wrapper'})

            # Регулярное выражение для поиска классов, начинающихся с 'listingcollapsed__item'
            regex_all = re.compile('listingcollapsed__item.*')
            # Поиск всех элементов, удовлетворяющих регулярному выражению
            try:
                all_products = soup.find_all('div', attrs={'class': 'listingcollapsed__activenumbercontainer'})
            except:
                continue
            # Выбор первого элемента
            try:
                first_product = all_products[0]
            except:
                continue
            try:
                find_product = first_product.find('a').get('data-id')
                print(f'{find_product} то что найдено')
            except:
                continue

            # with open(f"data.csv", 'a', newline='', encoding='utf-8') as csvfile:

            #     name_product = first_product.find_element(By.XPATH,
            #                                               ".//a[@data-test='activenumber,search-result-row-title']").get_attribute(
            #         "data-id")
            #     try:
            #         if name_product == value:
            #             try:
            #                 date_product = first_product.find_element(By.XPATH, './/div[@class="productdelivery__date"]').text
            #             except:
            #                 date_product = None
            #             try:
            #                 price_product = first_product.find_element(By.XPATH,
            #                                                './/div[@class="quantity quantity--pricesmall productpricetoggle__gross  productpricetoggle__wholesale  js-product-wholesale-toggle"]//div[@class="quantity__amount"]').text
            #             except:
            #                 price_product = None
            #             datas = [name_product, date_product, price_product]
            #             print(datas)
            # #             writer.writerow(datas)
            #     except:
            #         continue
    driver.close()
    driver.quit()


def parsing():
    driver = get_chromedriver_parsing()
    folders_html = fr"c:\DATA\intercars_eu\*.html"
    files_html = glob.glob(folders_html)
    coun = 0
    with open(f"data.csv", 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        for i in files_html:
            driver.get(i)
            coun += 1
            category = driver.find_element(By.XPATH, '//a[@data-test="parentCategoryName"]').get_attribute(
                "title").replace("/",
                                 "_")
            table_product = driver.find_element(By.XPATH, '//table[@class="listingcollapsed__wrapper"]')
            products = table_product.find_elements(By.XPATH, "//tbody[contains(@class, 'listingcollapsed__item')]")
            for i in products:
                name_product = i.find_element(By.XPATH,
                                              ".//a[@data-test='activenumber,search-result-row-title']").get_attribute(
                    "data-id")
                try:
                    date_product = i.find_element(By.XPATH, './/div[@class="productdelivery__date"]').text
                except:
                    date_product = None
                try:
                    price_product = i.find_element(By.XPATH,
                                                   './/div[@class="quantity quantity--pricesmall productpricetoggle__gross  productpricetoggle__wholesale  js-product-wholesale-toggle"]//div[@class="quantity__amount"]').text
                except:
                    price_product = None
                datas = [name_product, date_product, price_product]
                writer.writerow(datas)
            print(f"Осталось {len(files_html) - coun}")


if __name__ == '__main__':
    # get_category()
    get_product()
    # parsing()
