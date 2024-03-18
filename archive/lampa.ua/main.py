import json
import time
import csv

from fake_useragent import UserAgent
from selenium import webdriver
# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.chrome.service import Service
# Нажатие клавиш
from selenium.webdriver.common.by import By

# Библиотеки для Асинхронного парсинга
# Библиотеки для Асинхронного парсинга

useragent = UserAgent()
options = webdriver.ChromeOptions()
# Отключение режима WebDriver
options.add_experimental_option('useAutomationExtension', False)
# # Работа в фоновом режиме
# options.headless = True
options.add_argument(
    # "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
    f"user-agent={useragent.random}"
)
driver_service = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
driver = webdriver.Chrome(
    service=driver_service,
    options=options
)

# # Окно браузера на весь экран
driver.maximize_window()


# Для работы webdriver____________________________________________________


# Для работы undetected_chromedriver ---------------------------------------

# import undetected_chromedriver as uc
# driver = uc.Chrome()


# Для работы undetected_chromedriver ---------------------------------------


# "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0"

def get_url_category(url):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"

    }
    # driver.get(url=url)
    driver.get('https://www.lampa.ua/ru/katalog/43265.html')

    time.sleep(1)
    driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
    time.sleep(1)
    with open(f"data.html", "w", encoding='utf-8') as file:
        file.write(driver.page_source)
    exit()

    urls_category = driver.find_elements(By.XPATH,
                                         '//li[@class="nav-item level0 level-top nav-item--parent mega nav-item--only-subcategories parent"]//li[@class="nav-item level1 nav-item--only-subcategories parent"]//a')
    сard_url = []
    for items in urls_category:
        url_category = items.get_attribute('href')
        if items.get_attribute("href") != 'https://e27.com.ua/#':
            сard_url.append(
                {
                    'url_name': items.get_attribute("href")
                }
            )

        # Добавляем в словарь два параметра для дальнейшего записи в json
    with open("car_url.json", 'w') as file:
        json.dump(сard_url, file, indent=4, ensure_ascii=False)
    driver.close()
    driver.quit()


def get_url_product():
    with open(f"car_url.json") as file:
        all_site = json.load(file)
    products_url = []
    for item in all_site[:1]:
        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
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
    with open("products_url.json", 'w') as file:
        json.dump(products_url, file, indent=4, ensure_ascii=False)
    driver.close()
    driver.quit()


def parsing_product():
    with open(f"products_url.json") as file:
        all_site = json.load(file)
    products_url = []
    for item in all_site[:1]:
        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
        time.sleep(2)
        name_product_ru = driver.find_element(By.XPATH,
                                              '//div[@class="product-primary-column product-shop grid12-5"]//div[@class="product-name"]').text
        name_categorys = driver.find_elements(By.XPATH, '//div[@class="breadcrumbs"]//ul//li')
        name_category = name_categorys[-2].text
        sku_product = driver.find_element(By.XPATH, '//div[@class="sku"]//span[@class="value"]').text
        desk_product = driver.find_elements(By.XPATH, '//div[@class="short-description"]//ul//li')
        ch_01 = desk_product[0].text
        ch_02 = desk_product[1].text
        ch_03 = desk_product[2].text
        ch_04 = desk_product[3].text
        ch_05 = desk_product[4].text
        ch_06 = desk_product[5].text
        ch_07 = desk_product[6].text
        ch_08 = desk_product[7].text
        ch_09 = desk_product[8].text
        ch_10 = desk_product[9].text
        # ch_11 = desk_product[10].text
        with open(f"data.csv", "a", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    name_product_ru, name_category, sku_product, ch_02, ch_03, ch_04, ch_05, ch_06, ch_07,
                    ch_08, ch_09, ch_10

                )
            )
    driver.close()
    driver.quit()


def parse_content():
    url = "https://www.lampa.ua/"
    get_url_category(url)
    # get_url_product()
    # parsing_product()


if __name__ == '__main__':
    parse_content()
