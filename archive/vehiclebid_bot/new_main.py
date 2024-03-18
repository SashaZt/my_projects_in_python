import glob
import json
import time
from datetime import datetime
import zipfile

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# Нажатие клавиш

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки

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


def get_chromedriver(use_proxy=True, user_agent=None):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # chrome_options.headless = True

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


"""
Собираем все ссылки на товар
"""


def save_link_all_product(url):
    driver = get_chromedriver(use_proxy=True,
                              user_agent=f"{useragent.random}")

    # driver.get(url=url)
    # time.sleep(10)
    # Блок работы с куками-----------------------------------------
    # Создание куки
    # pickle.dump(driver.get_cookies(), open("cookies", "wb"))
    # Читание куки

    # Блок работы с куками-----------------------------------------
    card_url = []
    car_date = 0
    print('Введите дату в формате Год 2023, Месяц 01, День 25')
    print('*' * 50)
    print('Дата с какого числа')
    data_in = input()
    print('Дата по какое число')
    data_out = input()

    # Текущаяя дата
    # data_now = datetime.now().date()
    # exit()

    try:
        driver = get_chromedriver(use_proxy=True,
                                  user_agent=f"{useragent.random}")
        driver.get(f'{url}?yearFrom=1960&yearTo=2022&saleDateFrom={data_in}&saleDateTo={data_out}')
        if driver.find_element(By.XPATH, '//p[contains(text(), "Try changing the filters")]').text:
            print(f'С {data_in} по {data_out} объявлений нету')
        else:
            pagin_last = int(driver.find_element(By.XPATH, '//div[@class="css-1btdty2"]//a[last()]').text)
            for i in range(1, pagin_last + 1):
                # for cookie in pickle.load(open("cookies", "rb")):
                #     driver.add_cookie(cookie)
                if i == 1:
                    try:
                        driver = get_chromedriver(use_proxy=True,
                                                  user_agent=f"{useragent.random}")
                        driver.get(f'{url}?yearFrom=1960&yearTo=2022&saleDateFrom={data_in}&saleDateTo={data_out}')
                        if driver.find_element(By.XPATH, '//p[contains(text(), "Try changing the filters")]').text:
                            print(f'С {data_in} по {data_out} объявлений нету')
                            break
                        time.sleep(5)
                        url_cars = driver.find_elements(By.XPATH, '//div[@class="chakra-stack css-owjkmg"]/a')
                        for urls in url_cars:
                            data_sale = urls.find_element(By.XPATH,
                                                          '//div[@class="chakra-card__body css-1idwstw"]//p[@class="chakra-text css-0"][2]').text.replace(
                                'Дата продажи: ', '').replace('""', '')
                            card_url.append(
                                {
                                    'url_name': urls.get_attribute("href"),
                                    'data_sale': data_sale
                                }
                                # Добавляем в словарь два параметра для дальнейшего записи в json
                            )
                    except:
                        print(f'ошибка {url}')
                        time.sleep(1)
                        driver.close()
                        driver.quit()
                if i > 1:
                    try:
                        driver = get_chromedriver(use_proxy=True,
                                                  user_agent=f"{useragent.random}")

                        driver.get(
                            f'{url}?yearFrom=1960&yearTo=2022&saleDateFrom={data_in}&saleDateTo={data_out}&page={i}')
                        time.sleep(5)
                        if driver.find_element(By.XPATH, '//p[contains(text(), "Try changing the filters")]').text:
                            print(f'С {data_in} по {data_out} объявлений нету')
                            break
                        url_cars = driver.find_elements(By.XPATH, '//div[@class="chakra-stack css-owjkmg"]/a')
                        for urls in url_cars:
                            data_sale = urls.find_element(By.XPATH,
                                                          '//div[@class="chakra-card__body css-1idwstw"]//p[@class="chakra-text css-0"][2]').text.replace(
                                'Дата продажи: ', '').replace('""', '')
                            card_url.append(
                                {
                                    'url_name': urls.get_attribute("href"),
                                    'data_sale': data_sale
                                }
                                # Добавляем в словарь два параметра для дальнейшего записи в json
                            )
                        driver.close()
                        driver.quit()
                    except:
                        print(f'ошибка на странице {i}')
    except:
        print('+')
    with open("car_url.json", 'w') as file:
        json.dump(card_url, file, indent=4, ensure_ascii=False)

    #
    #
    #
    # for i in range(1, 3):
    #     # for cookie in pickle.load(open("cookies", "rb")):
    #     #     driver.add_cookie(cookie)
    #     if i == 1:
    #         try:
    #             driver = get_chromedriver(use_proxy=True,
    #                                       user_agent=f"{useragent.random}")
    #             driver.get(f'{url}?yearFrom=1960&yearTo=2022&saleDateFrom={data_in}&saleDateTo={data_out}')
    #             if driver.find_element(By.XPATH, '//p[contains(text(), "Try changing the filters")]').text:
    #                 print(f'С {data_in} по {data_out} объявлений нету')
    #                 break
    #             time.sleep(5)
    #             url_cars = driver.find_elements(By.XPATH, '//div[@class="chakra-stack css-owjkmg"]/a')
    #             for urls in url_cars:
    #                 data_sale = urls.find_element(By.XPATH,
    #                                               '//div[@class="chakra-card__body css-1idwstw"]//p[@class="chakra-text css-0"][2]').text.replace(
    #                     'Дата продажи: ', '').replace('""', '')
    #                 card_url.append(
    #                     {
    #                         'url_name': urls.get_attribute("href"),
    #                         'data_sale': data_sale
    #                     }
    #                     # Добавляем в словарь два параметра для дальнейшего записи в json
    #                 )
    #
    #             driver.close()
    #             driver.quit()
    #         except:
    #             print(f'ошибка {url}')
    #             time.sleep(1)
    #             driver.close()
    #             driver.quit()
    #     if i > 1:
    #         try:
    #             driver = get_chromedriver(use_proxy=True,
    #                                       user_agent=f"{useragent.random}")
    #
    #             driver.get(f'{url}?yearFrom=1960&yearTo=2022&saleDateFrom={data_in}&saleDateTo={data_out}')
    #             time.sleep(5)
    #             if driver.find_element(By.XPATH, '//p[contains(text(), "Try changing the filters")]').text:
    #                 print(f'С {data_in} по {data_out} объявлений нету')
    #                 break
    #             url_cars = driver.find_elements(By.XPATH, '//div[@class="chakra-stack css-owjkmg"]/a')
    #             for urls in url_cars:
    #                 data_sale = urls.find_element(By.XPATH,
    #                                               '//div[@class="chakra-card__body css-1idwstw"]//p[@class="chakra-text css-0"][2]').text.replace(
    #                     'Дата продажи: ', '').replace('""', '')
    #                 card_url.append(
    #                     {
    #                         'url_name': urls.get_attribute("href"),
    #                         'data_sale': data_sale
    #                     }
    #                     # Добавляем в словарь два параметра для дальнейшего записи в json
    #                 )
    #             driver.close()
    #             driver.quit()
    #         except:
    #             print(f'ошибка на странице {i}')
    #     car_date += 1
    #
    # print(car_date)
    # with open("car_url.json", 'w') as file:
    #     json.dump(card_url, file, indent=4, ensure_ascii=False)
    #


"""
Сохраняем все страницы
"""


def save_html_page():
    # Читание json
    with open(f"car_url.json") as file:
        all_site = json.load(file)
    # С json вытягиваем только 'url_name' - это и есть ссылка
    # Путь ко всем файлам
    targetPattern = f"C:\\scrap_tutorial-master\\vehiclebid_bot\\data\\*.html"
    """
    сранение двух списков
    """
    # Создаем список всех файлов
    files_html = glob.glob(targetPattern)
    # Создаем список файлов только по уникальному номеру, это последняя цифры
    list_html_files = []
    for item_files in files_html:
        list_html_files.append(item_files.split("\\")[-1].replace(".html", ""))
    # Создаем спискок только url
    url_car = []
    new_url_car = []
    #
    for item_url in all_site:
        url_car.append(item_url['url_name'])
    for item in url_car:
        if item.split("-")[-1] in list_html_files:
            continue
        else:
            new_url_car.append(item)
    for href in new_url_car:
        driver = get_chromedriver(use_proxy=True,
                                  user_agent=f"{useragent.random}")
        try:
            driver.get(href)
            driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
            time.sleep(5)
            LOT = driver.find_element(By.XPATH, '//ul[@class="css-tu0njr"]//li[last()]').text.replace(
                "LOT Номер: ",
                "")
            with open(f"C:\\scrap_tutorial-master\\vehiclebid_bot\\data\\{LOT}.html", "w", encoding='utf-8') as file:
                file.write(driver.page_source)
            time.sleep(1)
            print(f'сохранил {LOT}.html')
            driver.close()
            driver.quit()
        except:
            print(f'ошибка на {href}')
            time.sleep(1)
            driver.close()
            driver.quit()
    print('Все страницы сохранены')


"""
Извлечение информации с каждой страницы html
"""


def scrap_html_page():
    targetPattern = f"C:/scrap_tutorial-master/vehiclebid_bot/data/*.html"
    files_html = glob.glob(targetPattern)
    options = webdriver.ChromeOptions()
    driver_service = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    # Работа в фоновом режиме
    options.headless = True
    driver = webdriver.Chrome(
        service=driver_service,
        options=options
    )

    for item in files_html:
        driver.get(item)
        all_link_img = []
        # Часть названия класса contains
        image = driver.find_elements(By.XPATH, '//div[contains(@class,"swiper-slide swiperSlide")]//img')
        for h in image:
            all_link_img.append(h.get_attribute("src"))
        # Обьеденяим их в одну сроку, разделитель указываем в начале
        link_img = " ; ".join(all_link_img)
        print(link_img)
        # car_vin = driver.find_element(By.XPATH, '//div[@class="css-1giup7d"]//h1').text
        # car_price = driver.find_element(By.XPATH, '//div[@class="css-1giup7d"]//p').text
        # car_values = driver.find_elements(By.XPATH, '//div[@class="css-1bntj9o"]')
        # car_value_1 = car_values[0].get_attribute('outerText').replace("\n", " ")
        # car_value_2 = car_values[1].get_attribute('outerText').replace("\n", " ")
        # car_value_3 = car_values[2].get_attribute('outerText').replace("\n", " ")
        # car_value_4 = car_values[3].get_attribute('outerText').replace("\n", " ")
        # car_value_5 = car_values[4].get_attribute('outerText').replace("\n", " ")
        # car_value_6 = car_values[5].get_attribute('outerText').replace("\n", " ")
        # car_value_7 = car_values[6].get_attribute('outerText').replace("\n", " ")
        # car_value_8 = car_values[7].get_attribute('outerText').replace("\n", " ")
        # car_value_9 = car_values[8].get_attribute('outerText').replace("\n", " ")
        # car_value_10 = car_values[9].get_attribute('outerText').replace("\n", " ")
        # car_value_11 = car_values[10].get_attribute('outerText').replace("\n", " ")
        # print(
        #     f'{car_vin} | {car_price} | {car_value_1} | {car_value_2} | {car_value_3} | {car_value_4} | {car_value_5} | {car_value_6} | {car_value_7} | {car_value_8} | {car_value_9} | {car_value_10} | {car_value_11}')
    driver.close()
    driver.quit()


if __name__ == '__main__':
    # # Собираем все ссылки на товаров
    url = "https://vehiclebid.info/ru/search"
    save_link_all_product(url)
    # Парсим все товары из файлов с
    ## Сохранение html страниц каждой машины
    # save_html_page()
    ## Извлечение информации с каждой страницы html
    # scrap_html_page()
"""
 # with open(f"{item}", encoding="utf-8") as file:
        #     src = file.read()
        # soup = BeautifulSoup(src, 'lxml')
        # car_vin = soup.find('div', attrs={'class': 'css-1giup7d'}).find('h1').text
        # car_price = soup.find('div', attrs={'class': 'css-1giup7d'}).find('p').text
        # car_values = soup.find_all('div', attrs={'class': 'css-1bntj9o'})
        # car_value_1 = car_values[0].text
        # car_value_2 = car_values[1].text
        # car_value_3 = car_values[2].text
        # car_value_4 = car_values[3].text
        # car_value_5 = car_values[4].text
        # car_value_6 = car_values[5].text
        # car_value_7 = car_values[6].text
        # car_value_8 = car_values[7].text
        # car_value_9 = car_values[8].text
        # car_value_10 = car_values[9].text
        # car_value_11 = car_values[10].text

        # print(
        #     f'{car_vin} | {car_price} | {car_value_1} | {car_value_2} | {car_value_3} | {car_value_4} | {car_value_5} | {car_value_6} | {car_value_7} | {car_value_8} | {car_value_9} | {car_value_10} | {car_value_11}')
"""
