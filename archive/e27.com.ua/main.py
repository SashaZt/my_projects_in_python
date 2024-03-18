import zipfile
import json
import time
import csv
import re
import datetime
import pandas as pd

from fake_useragent import UserAgent
from selenium import webdriver
# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.chrome.service import Service
# Нажатие клавиш
from selenium.webdriver.common.by import By

# Библиотеки для Асинхронного парсинга

useragent = UserAgent()
# options = webdriver.ChromeOptions()
# # Отключение режима WebDriver
# options.add_experimental_option('useAutomationExtension', False)
# # # Работа в фоновом режиме
# # options.headless = True
# options.add_argument(
#     # "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
#     f"user-agent={useragent.random}"
# )
# driver_service = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
# driver = webdriver.Chrome(
#     service=driver_service,
#     options=options
# )
#
# # # Окно браузера на весь экран
# driver.maximize_window()

# Для работы webdriver____________________________________________________


# Для работы undetected_chromedriver ---------------------------------------

# import undetected_chromedriver as uc
# driver = uc.Chrome()


# Для работы undetected_chromedriver ---------------------------------------


# "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0"


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
        # не открывается браузер
        # chrome_options.headless = True
        ##Необходимо тестировать!!!
        # chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # chrome_options.add_experimental_option('useAutomationExtension', False)

    if user_agent:
        chrome_options.add_argument(f'--user-agent={user_agent}')

    s = Service(
        executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )
    ##Необходимо тестировать!!!
    # driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    #     'source': '''
    #                 delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
    #                 delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
    #                 delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    #           '''
    # })

    return driver


def get_url_category(url):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"

    }
    driver = get_chromedriver(use_proxy=True,
                              user_agent=f"{useragent.random}")
    # driver.get(url=url)
    driver.get('https://e27.com.ua/imperium-light-398165-45-91.html')

    time.sleep(1)
    driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
    with open(f"C:\\scrap_tutorial-master\\e27.com.ua\\data.html", "w", encoding='utf-8') as file:
        file.write(driver.page_source)

    urls_category = driver.find_elements(By.XPATH,
                                         '//li[@class="nav-item level0 level-top nav-item--parent mega nav-item--only-subcategories parent"]//li[@class="nav-item level1 nav-item--only-subcategories parent"]//a')
    сard_url = []
    # Искллючение которые не нужно добавлять в список
    ex_01 = 'https://e27.com.ua/#'
    ex_02 = 'https://e27.com.ua/track-luminaires'
    ex_03 = 'https://e27.com.ua/chandeliers'
    ex_04 = 'https://e27.com.ua/wall-luminaires'
    ex_05 = 'https://e27.com.ua/pendants'
    ex_06 = 'https://e27.com.ua/table-lamps'
    ex_07 = 'https://e27.com.ua/ceilings'
    ex_08 = 'https://e27.com.ua/floor-lamps'
    ex_09 = 'https://e27.com.ua/spot-luminaires'
    ex_10 = 'https://e27.com.ua/other-luminaires'
    ex_11 = 'https://e27.com.ua/spots'
    ex_12 = 'https://e27.com.ua/spotlights'
    ex_13 = 'https://e27.com.ua/magnetic-track-systems'
    ex_14 = 'https://e27.com.ua/1-phase-track-systems'
    ex_15 = 'https://e27.com.ua/3-phase-track-systems'
    # В цикле перебираем все ссылки, если есть исключение, тогда не добавляем в общий список
    for items in urls_category[:122]:
        url_category = items.get_attribute('href')
        if items.get_attribute("href") != ex_01 and items.get_attribute(
                "href") != ex_02 and items.get_attribute(
            "href") != ex_03 and items.get_attribute(
            "href") != ex_04 and items.get_attribute(
            "href") != ex_05 and items.get_attribute(
            "href") != ex_06 and items.get_attribute(
            "href") != ex_07 and items.get_attribute(
            "href") != ex_08 and items.get_attribute(
            "href") != ex_09 and items.get_attribute(
            "href") != ex_10 and items.get_attribute(
            "href") != ex_11 and items.get_attribute(
            "href") != ex_12 and items.get_attribute(
            "href") != ex_13 and items.get_attribute(
            "href") != ex_14 and items.get_attribute(
            "href") != ex_15:
            сard_url.append(
                {
                    'url_name': items.get_attribute("href")
                }
            )

        # Добавляем в словарь два параметра для дальнейшего записи в json

    with open("car_url.json", 'w') as file:
        json.dump(сard_url, file, indent=4, ensure_ascii=False)
    print('Файл car_url.json с сылками записан')
    driver.close()
    driver.quit()


def get_url_product():
    driver = get_chromedriver(use_proxy=True,
                              user_agent=f"{useragent.random}")
    with open(f"car_url.json") as file:
        all_site = json.load(file)
    products_url = []
    for item in all_site[:1]:
        driver.get(f'{item["url_name"]}?limit=72')  # 'url_name' - это и есть ссылка
        time.sleep(2)
        isNextDisable = False
        while not isNextDisable:
            try:
                # ----------------------------------------------------------
                # Если необходимо сначала прогрузить все товары тогда открываем все и только потом получаем ссылки
                # Сначала что то ищем на первой странице, а только потом ищем на остальных
                urls_product = driver.find_elements(By.XPATH,
                                                    '//ul[@class="products-grid category-products-grid itemgrid itemgrid-adaptive itemgrid-3col single-line-name centered hover-effect equal-height"]//li[@class="item"]//div[@class="product-image-wrapper"]/a')
                time.sleep(2)
                for i in urls_product:
                    url_product = i.get_attribute("href")
                    products_url.append(
                        {
                            'url_name': url_product
                        }
                    )
                # Если необходимо подождать елемент тогда WebDriverWait
                # next_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//i[@class="fa fa-chevron-right"]')))
                # driver.implicitly_wait(5)
                # Опускаемя в самый низ страницы
                # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                next_button = driver.find_element(By.XPATH,
                                                  '//div[@class="toolbar-bottom pager-center"]//li[@class="next"]')
                driver.execute_script("window.scrollBy(0,2000)", "")
                # Прокручиваем пока не найдем элемент
                # driver.execute_script("arguments[0].scrollIntoView();",next_button)
                # # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!
                # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                if next_button:
                    next_button.click()
                else:
                    isNextDisable = True
            except:
                isNextDisable = True
        # Листать по страницам ---------------------------------------------------------------------------
        file_category = item["url_name"].split("/")[-1]
        with open(f"{file_category}.json", 'a') as file:
            json.dump(products_url, file, indent=4, ensure_ascii=False)
    print('Файл products_url.json с сылками записан')
    driver.close()
    driver.quit()


def parsing_product():
    driver = get_chromedriver(use_proxy=True,
                              user_agent=f"{useragent.random}")
    start_time = datetime.datetime.now()
    with open(f"chandeliers-ceilings.json") as file:
        all_site = json.load(file)
    products_url = []
    for item in all_site[3:6]:

        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка

        # driver.get('C:\\scrap_tutorial-master\\e27.com.ua\\data.html')
        name_product_ru = driver.find_element(By.XPATH,
                                              '//div[@class="product-primary-column product-shop grid12-5"]//div[@class="product-name"]').text
        name_categorys = driver.find_elements(By.XPATH, '//div[@class="breadcrumbs"]//ul//li')
        name_category = name_categorys[-2].text
        sku_product = driver.find_element(By.XPATH, '//div[@class="sku"]//span[@class="value"]').text
        desk_list_all = []
        # Все описание
        desk_product = driver.find_elements(By.XPATH, '//div[@class="short-description"]//ul//li')

        for i in desk_product[1:]:
            if i.text in "Плафо":
                print(i.text)
    exit()
    # # for i in desk_product:
    # #     desk_list_all.append(i.text)
    # # desk_list = " ; ".join(desk_list_all)
    # # print(desk_list)
    # # with open(f"C:\\scrap_tutorial-master\\e27.com.ua\\data_.csv", "a", errors='ignore') as file:
    # #     writer = csv.writer(file, delimiter=";", lineterminator="\r")
    # #     writer.writerow(
    # #         (desk_list
    # #          ))
    # # exit()
    # regex_ch_10 = 'Страна регистрац'
    # regex_ch_11 = 'Страна производ'
    # try:
    #     if desk_product[1]:
    #         ch_02 = desk_product[1].text.replace("Размеры: ", "Размеры / ").replace(" см.", "").split(" / ")
    #     else:
    #         print(f'ch_02_{sku_product}')
    # except:
    #     ch_02 = ""
    # try:
    #     ch_02_01 = ch_02[0]
    # except:
    #     ch_02_01 = ""
    # try:
    #     ch_02_02 = ch_02[1]
    # except:
    #     ch_02_02 = ""
    # try:
    #     ch_02_03 = ch_02[2]
    # except:
    #     ch_02_03 = ""
    # try:
    #     ch_02_04 = ch_02[3]
    # except:
    #     ch_02_04 = ""
    # # Лампы: 3шт x 40Вт (E14)
    # try:
    #     if desk_product[2]:
    #         ch_03 = desk_product[2].text.replace("Лампы: ", "Лампы / ").replace(" x ", " / ").replace(" (",
    #                                                                                                   " / (").split(
    #             " / ")
    #     else:
    #         print(f'ch_03_{sku_product}')
    # except:
    #     ch_03 = ""
    # try:
    #     ch_03_01 = ch_03[0]
    # except:
    #     ch_03_01 = ""
    # try:
    #     ch_03_02 = ch_03[1]
    # except:
    #     ch_03_02 = ""
    # try:
    #     ch_03_03 = ch_03[2]
    # except:
    #     ch_03_03 = ""
    # try:
    #     ch_03_04 = ch_03[3]
    # except:
    #     ch_03_04 = ""
    # # Плафон: Стекло / Белый (white).
    # try:
    #     if desk_product[3]:
    #         ch_04 = desk_product[3].text.replace("Плафон: ", "Плафон /").split("/")
    #     else:
    #         print(f'ch_04_{sku_product}')
    # except:
    #     ch_04 = ""
    # regex_ch_04_01 = 'Плафон'
    # try:
    #     if regex_ch_04_01 in ch_04[0]:
    #         ch_04_01 = ch_04[0]
    #     else:
    #         ch_04_01 = ""
    # except:
    #     print(f'ch_04_01{sku_product}')
    # try:
    #     ch_04_02 = ch_04[1]
    # except:
    #     ch_04_02 = ""
    # try:
    #     ch_04_03 = ch_04[2]
    # except:
    #     ch_04_03 = ""
    # # Основание: Металл ; Стальной матовый.
    # try:
    #     if desk_product[4]:
    #         ch_05 = desk_product[4].text.replace("Основание: ", "Основание / ").split(" / ")
    #     else:
    #         print(f'ch_04_{sku_product}')
    # except:
    #     ch_05 = ""
    #
    # regex_ch_05_01 = 'Основани'
    # try:
    #     if regex_ch_05_01 in ch_05[0]:
    #         ch_05_01 = ch_05[0]
    #     else:
    #         ch_05_01 = ""
    # except:
    #     ch_05_01 = ""
    # try:
    #     ch_05_02 = ch_05[1]
    # except:
    #     ch_05_02 = ""
    # try:
    #     ch_05_03 = ch_05[2]
    # except:
    #     ch_05_03 = ""
    # regex_ch_08 = 'Лампа'
    # regex_ch_06 = 'Совместимос'
    # regex_ch_09 = 'Питание'
    # try:
    #     if regex_ch_06 in desk_product[5].text:
    #         ch_06 = desk_product[5].text
    #     elif regex_ch_08 in desk_product[5].text:
    #         ch_08 = desk_product[5].text
    #     else:
    #         ch_06 = None
    # except:
    #     ch_06 = None
    #
    # regex_ch_07 = 'Уровень за'
    # try:
    #     if regex_ch_07 in desk_product[6].text:
    #         ch_07 = desk_product[6].text
    #     elif regex_ch_09 in desk_product[6].text:
    #         ch_09 = desk_product[6].text
    #     else:
    #         ch_07 = desk_product[6].text
    # except:
    #     ch_07 = None
    #
    # try:
    #     if regex_ch_08 in desk_product[7].text:
    #         ch_08 = desk_product[7].text
    #     elif regex_ch_10 in desk_product[7].text:
    #         ch_10 = desk_product[7].text
    #     else:
    #         ch_08 = desk_product[7].text
    #
    # except:
    #     ch_08 = None
    #
    # regex_ch_09 = 'Питание'
    # try:
    #     if regex_ch_09 in desk_product[8].text:
    #         ch_09 = desk_product[8].text
    #     else:
    #         ch_09 = desk_product[8].text
    # except:
    #     ch_09 = None
    #
    # "regex_ch_10 = 'Страна регистрац'"
    # try:
    #     if regex_ch_10 in desk_product[9].text:
    #         ch_10 = desk_product[9].text
    #     elif desk_product[9].text == None:
    #         ch_10 = desk_product[7].text
    #
    #     # if regex_ch_10 in desk_product[9].text:
    #     #     ch_10 = desk_product[9].text
    #     # elif regex_ch_11 in desk_product[9].text:
    #     #     ch_10 = desk_product[8].text
    #     # else:
    #     #     ch_10 = desk_product[7].text
    # except:
    #     ch_10 = None
    #
    # "regex_ch_11 = 'Страна производ'"
    # try:
    #     ch_11 = desk_product[10].text
    #     # if regex_ch_11 in desk_product[10].text:
    #     #     ch_11 = desk_product[10].text
    #     # elif regex_ch_10 in desk_product[10].text:
    #     #     ch_11 = desk_product[10].text
    #     # else:
    #     #     ch_11 = desk_product[8].text
    # except:
    #     ch_11 = None
    # print(sku_product)
    # print(f'ch_06 - {ch_06}')
    # print(f'ch_07 - {ch_07}')
    # print(f'ch_08 - {ch_08}')
    # print(f'ch_09 - {ch_09}')
    # print(f'ch_10 - {ch_10}')
    # print(f'ch_11 - {ch_11}')
    #
    # print("*" * 50)
    # #
    # # d1 = {'Название': [name_product_ru], 'Категория': [name_category], 'Артикул': [sku_product],
    # #       'ch_02_01': [ch_02_01], 'ch_02_02': [ch_02_02], 'ch_02_03': [ch_02_03], 'ch_02_04': [ch_02_04],
    # #       'ch_03_01': [ch_03_01], 'ch_03_02': [ch_03_02], 'ch_03_03': [ch_03_03], 'ch_03_04': [ch_03_04],
    # #       'ch_04_01': [ch_04_01], 'ch_04_02': [ch_04_02], 'ch_04_03': [ch_04_03], 'ch_05_01': [ch_05_01],
    # #       'ch_05_02': [ch_05_02], 'ch_05_03': [ch_05_03], 'ch_06': [ch_06], 'ch_07': [ch_07], 'ch_08': [ch_08],
    # #       'ch_09': [ch_09], 'ch_10': [ch_10], 'ch_11': [ch_11]}
    # # df = pd.DataFrame(d1)
    # # # print(df)
    # # with open(f"C:\\scrap_tutorial-master\\e27.com.ua\\data_.csv", "w") as csv_file:
    # #     df.to_csv(f"C:\\scrap_tutorial-master\\e27.com.ua\\data.csv",
    # #               encoding='cp1251',
    # #               mode='a',
    # #               header=True,
    # #               index=False,
    # #               sep=';'
    # #               )
    # #
    # # with open(f"C:\\scrap_tutorial-master\\e27.com.ua\\data.csv", "a", errors='ignore') as file:
    # #     writer = csv.writer(file, delimiter=";", lineterminator="\r")
    # #     writer.writerow(
    # #         (
    # #             name_product_ru, name_category, sku_product, ch_02_01, ch_02_02, ch_02_03, ch_02_04, ch_03_01,
    # #             ch_03_02, ch_03_03, ch_03_04, ch_04_01, ch_04_02, ch_04_03, ch_05_01, ch_05_02, ch_05_03, ch_06,
    # #             ch_07, ch_08, ch_09, ch_10, ch_11
    # #
    # #         )
    # #     )

    diff_time = datetime.datetime.now() - start_time
    print(diff_time)
    driver.close()
    driver.quit()


def parse_content():
    # url = "https://e27.com.ua/"
    # get_url_category(url)
    # get_url_product()
    parsing_product()


if __name__ == '__main__':
    parse_content()
