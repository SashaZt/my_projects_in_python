import zipfile
import os
import json
import csv
import time
import requests
# Нажатие клавиш
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from selenium import webdriver
import random
from fake_useragent import UserAgent

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

useragent = UserAgent()

# Данные для прокси
PROXY_HOST = '141.145.205.4'
PROXY_PORT = 31281
PROXY_USER = 'proxy_alex'
PROXY_PASS = 'DbrnjhbZ88'

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
        executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )

    return driver


def main(url):
    driver = get_chromedriver(use_proxy=True,
                              user_agent=f"{useragent.random}")
    driver.get(url)
    group = url.split("/")[-2]
    product_url = []
    with open(f"C:\\scrap_tutorial-master\\lovely-professional\\{group}.csv", "w", errors='ignore') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                'name_product',
                'price',
                'description',
                'image_01',
                'image_02',
                'image_03'

            )
        )
    # Блок работы с куками-----------------------------------------
    # Создание куки
    # pickle.dump(driver.get_cookies(), open("cookies", "wb"))
    # Читание куки
    # for cookie in pickle.load(open("cookies", "rb")):
    #     driver.add_cookie(cookie)
    # Блок работы с куками-----------------------------------------

    # Листать по страницам ---------------------------------------------------------------------------
    page_product = 0
    isNextDisable = False
    while not isNextDisable:
        try:
            # ----------------------------------------------------------
            # Если необходимо сначала прогрузить все товары тогда открываем все и только потом получаем ссылки
            # Сначала что то ищем на первой странице, а только потом ищем на остальных
            # card_product_url = driver.find_elements(By.XPATH, '//div[@class="catalog-section-item-name"]/a')
            # for item in card_product_url[0:13]:
            #     product_url.append(
            #         {'url_name': item.get_attribute("href")}
            #         # Добавляем в словарь два параметра для дальнейшего записи в json
            #     )
            #     print(item.get_attribute("href"))
            # Если необходимо подождать елемент тогда WebDriverWait
            # next_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//i[@class="fa fa-chevron-right"]')))
            driver.implicitly_wait(5)
            next_button = driver.find_element(By.XPATH, '//div[@class="catalog-section-more-text intec-cl-text"]')
            # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            if next_button:
                next_button.click()
            else:
                isNextDisable = True
        except:
            isNextDisable = True
    # Листать по страницам ---------------------------------------------------------------------------
    # Получаем ссылки
    card_product_url = driver.find_elements(By.XPATH, '//div[@class="catalog-section-item-name"]/a')
    for item in card_product_url:
        product_url.append(
            {'url_name': item.get_attribute("href")}
            # Добавляем в словарь два параметра для дальнейшего записи в json
        )

    # Проверяем на существование файла, если нету тогда записываем в json
    if os.path.exists(f"{group}.json"):
        print(f"C:\\scrap_tutorial-master\\lovely-professional\\{group}.json" + " уже существует")
    else:
        with open(f"C:\\scrap_tutorial-master\\lovely-professional\\{group}.json", 'w') as file:
            json.dump(product_url, file, indent=4, ensure_ascii=False)

    # Читание json
    with open(f"C:\\scrap_tutorial-master\\lovely-professional\\{group}.json") as file:
        all_site = json.load(file)
    # С json вытягиваем только 'url_name' - это и есть ссылка
    product_sum = 0
    for item in all_site:
        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
        try:
            name_product = driver.find_element(By.XPATH, '//div[@class="intec-content-wrapper"]/h1').text.replace('"',
                                                                                                                  '').replace(
                '/ №', '').replace('*', '_')  # удаляем из названия следующие символы
        except:
            name_product = 'No name'
        try:
            price_product = driver.find_element(By.XPATH, '//div[@class="catalog-element-price-discount"]').text
        except:
            price_product = "No price"
        try:
            descript_products = driver.find_element(By.XPATH, '//div[@class="product_description"]').text.replace("\n",
                                                                                                                  "")  # Убираем перенос с описания
        except:
            descript_products = "No description"
        img_list = []
        try:
            img_product = driver.find_elements(By.XPATH, '//img[@role="presentation"]')
            for i in img_product:
                img_list.append(i.get_attribute("src"))

        except:
            img_list[0] = "No foto"
            img_list[1] = "No foto"

        # выкачиваем фото через requests
        for href in img_list:
            # print(href)
            img_data = requests.get(href, proxies=proxies)
            with open(
                    f"C:\\scrap_tutorial-master\\lovely-professional\\{group}\\{name_product}_{random.randint(1, 100)}.jpg",
                    'wb') as handler:
                handler.write(img_data.content)

        if len(img_list) == 1:
            with open(f"C:\\scrap_tutorial-master\\lovely-professional\\{group}.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow(
                    (
                        name_product,
                        price_product,
                        descript_products,
                        img_list[0]
                    )
                )
        elif len(img_list) == 2:
            with open(f"C:\\scrap_tutorial-master\\lovely-professional\\{group}.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow(
                    (
                        name_product,
                        price_product,
                        descript_products,
                        img_list[0],
                        img_list[1]

                    )
                )
        elif len(img_list) == 3:
            with open(f"C:\\scrap_tutorial-master\\lovely-professional\\{group}.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow(
                    (
                        name_product,
                        price_product,
                        descript_products,
                        img_list[0],
                        img_list[1],
                        img_list[2]

                    )
                )
        elif len(img_list) == 4:
            with open(f"C:\\scrap_tutorial-master\\lovely-professional\\{group}.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow(
                    (
                        name_product,
                        price_product,
                        descript_products,
                        img_list[0],
                        img_list[1],
                        img_list[2],
                        img_list[3]

                    )
                )
        elif len(img_list) == 5:
            with open(f"C:\\scrap_tutorial-master\\lovely-professional\\{group}.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow(
                    (
                        name_product,
                        price_product,
                        descript_products,
                        img_list[0],
                        img_list[1],
                        img_list[2],
                        img_list[3],
                        img_list[4]

                    )
                )
        elif len(img_list) == 9:
            with open(f"C:\\scrap_tutorial-master\\lovely-professional\\{group}.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow(
                    (
                        name_product,
                        price_product,
                        descript_products,
                        img_list[0],
                        img_list[1],
                        img_list[2],
                        img_list[3],
                        img_list[4],
                        img_list[5],
                        img_list[6],
                        img_list[7],
                        img_list[8]
                    )
                )
        elif len(img_list) == 8:
            with open(f"C:\\scrap_tutorial-master\\lovely-professional\\{group}.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow(
                    (
                        name_product,
                        price_product,
                        descript_products,
                        img_list[0],
                        img_list[1],
                        img_list[2],
                        img_list[3],
                        img_list[4],
                        img_list[5],
                        img_list[6],
                        img_list[7]
                    )
                )
        elif len(img_list) == 11:
            with open(f"C:\\scrap_tutorial-master\\lovely-professional\\{group}.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow(
                    (
                        name_product,
                        price_product,
                        descript_products,
                        img_list[0],
                        img_list[1],
                        img_list[2],
                        img_list[3],
                        img_list[4],
                        img_list[5],
                        img_list[6],
                        img_list[7],
                        img_list[8],
                        img_list[9],
                        img_list[10]
                    )
                )
        # product_sum += 1
        # print(item['url_name'])
        # print(f"Обработано {product_sum} найменования")
        # print(f"количество фото {len(img_list)}")

    driver.close()
    driver.quit()


if __name__ == '__main__':
    url = "http://www.lovely-professional.com/catalog/brow_euro/"
    main(url)
