import csv
import glob
import json
import zipfile

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait

# Нажатие клавиш

useragent = UserAgent()

# Данные для прокси
PROXY_HOST = 'IP'
PROXY_PORT = 'PORT' #Без кавычек
PROXY_USER = 'LOGIN'
PROXY_PASS = 'PASS'

# Настройка для requests чтобы использовать прокси
proxies = {'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}/'}

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
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"76.0.0"
}
"""

background_js = """
let config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
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
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

def get_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()

    if use_proxy:
        plugin_file = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr('manifest.json', manifest_json)
            zp.writestr('background.js', background_js)

        chrome_options.add_extension(plugin_file)

    if user_agent:
        chrome_options.add_argument(f'--user-agent={user_agent}')

    s = Service(
        executable_path="D:\\Парсер\\demex.com.ua\\chromedriver.exe"
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )

    return driver


def save_link_all_product(url):
    driver = get_chromedriver(use_proxy=False,
                              user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')
    driver.get(url=url)

    driver.maximize_window()
    button_find = WebDriverWait(driver, 200).until(
        EC.element_to_be_clickable((By.XPATH, '//i[@class="iconcar-search"]')))
    products_all_url = []
    categoriy_product_urls = []
    pod_categoriy_product_urls = []
    card_product_url_all = []
    categoriy_product_url = driver.find_elements(By.XPATH, '//ul[@class="wsdown-mobile wsdownmenu-list wsmenu-list"]//a')
    for item_categoriy in categoriy_product_url:

        categoriy_product_urls.append(
            {'url_name': item_categoriy.get_attribute("href")}
        )
    # Тут категории все
    for item_prod in categoriy_product_urls[331:]:
        driver.get(item_prod['url_name'])
        group = item_prod['url_name'].split("/")[-1]

        button_find = WebDriverWait(driver, 200).until(
            EC.element_to_be_clickable((By.XPATH, '//i[@class="iconcar-search"]')))
        # Листать по страницам ---------------------------------------------------------------------------
        isNextDisable = False
        while not isNextDisable:
            try:
                card_product_url = driver.find_elements(By.XPATH, '//div[@class="product-name"]//a')
                for hrefs in card_product_url:
                    products_all_url.append(
                        {'url_name': hrefs.get_attribute("href")}
                    )

                next_button = driver.find_element(By.XPATH, '//div[@class="pagination"]//li//a[@class="page_next"]')
                driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")

                # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!
                if next_button:
                    next_button.click()
                    # time.sleep(1)
                    # driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
                else:
                    isNextDisable = True
            except:
                isNextDisable = True
        # Листать по страницам ---------------------------------------------------------------------------

        with open(f"D:\\Парсер\\demex.com.ua\\{group}.json", 'a') as file:
            json.dump(products_all_url, file, indent=4, ensure_ascii=False)

    driver.close()
    driver.quit()


def parsing_product():
    # Получаем список файлов с сылками на товары
    targetPattern = r"D:\Парсер\demex.com.ua\*.json"
    files_json = glob.glob(targetPattern)
    for item in files_json:
        with open(f"{item}") as file:
            group = item.split("\\")[-1].replace(".json", "")
            all_site = json.load(file)

        # Переходим по каждой ссылке товара и получаем данные
        for href_card in all_site:
            driver = get_chromedriver(use_proxy=False,
                                      user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')


            driver.get(href_card['url_name'])  # 'url_name' - это и есть ссылка

            driver.maximize_window()
            button_find = WebDriverWait(driver, 200).until(
                EC.element_to_be_clickable((By.XPATH, '//i[@class="iconcar-search"]')))

            try:
                name_product = driver.find_element(By.XPATH,'//h1[@class="title-item"]').text
            except:
                name_product = 'Not title'
            try:
                categ_product = driver.find_elements(By.XPATH, '//span[@itemprop="name"]')
                bread = categ_product[-2].text

            except:
                categ_product = "Not categ_product"
            try:
                price_new = driver.find_element(By.XPATH,
                                                '//span[@class="price-val"]').text
            except:
                price_new = 'no price_old'

            # Получаем ссылки на все фото и добавляем их в словарь
            all_link_img = []
            image = driver.find_elements(By.XPATH,
                                         '//div[@class="col-md-4 popup-gallery"]//a')
            for h in image:
                all_link_img.append(h.get_attribute("href"))
            # Обьеденяим их в одну сроку, разделитель указываем в начале
            link_img = " ; ".join(all_link_img)
            try:
                desk_product = driver.find_element(By.XPATH, '//dl[@class="dl-horizontal dl-criteria m-no "]').get_attribute('innerText').replace("\n", " ")
            except:
                desk_product = 'not desk_product'
            try:
                original_nomer = driver.find_element(By.XPATH, '//div[@id="case_oem"]').get_attribute("innerText").replace("\n", " ")
            except:
                original_nomer = 'not original_nomer'


            # print(name_product, bread, price_new, link_img, desk_product, original_nomer)
            with open(f"D:\\Парсер\\demex.com.ua\\{group}.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow(
                    (
                        href_card['url_name'], name_product, bread, price_new, link_img, desk_product, original_nomer

                    )
                )

        driver.close()
        driver.quit()


if __name__ == '__main__':
    # # Собираем все ссылки на категории товаров
    url = "https://demex.com.ua/"
    save_link_all_product(url)
    #Парсим все товары из файлов с
    parsing_product()
