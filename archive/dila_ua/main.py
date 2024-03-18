import datetime
import json
import csv
import pickle
import lxml
import time
# Нажатие клавиш
from selenium.webdriver.common.keys import Keys
from random import randint
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import csv
from selenium import webdriver
import random
from fake_useragent import UserAgent

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

useragent = UserAgent()
options = webdriver.ChromeOptions()
# Отключение режима WebDriver
options.add_experimental_option('useAutomationExtension', False)

# # Работа в фоновом режиме
options.headless = True

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
# driver.maximize_window()


# Для работы webdriver____________________________________________________


# Для работы undetected_chromedriver ---------------------------------------

# import undetected_chromedriver as uc
# driver = uc.Chrome()


# Для работы undetected_chromedriver ---------------------------------------


# "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0"

def get_content(url):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"

    }

    try:
        start_time = datetime.datetime.now()
        driver.get(url=url)
        analysis_list = []
        # Блок работы с куками-----------------------------------------
        # Создание куки
        # pickle.dump(driver.get_cookies(), open("cookies", "wb"))
        # Читание куки
        # for cookie in pickle.load(open("cookies", "rb")):
        #     driver.add_cookie(cookie)
        # Блок работы с куками-----------------------------------------
        driver.implicitly_wait(10)
        drop_list_city = driver.find_element(By.XPATH, '//div[@id="js_sel_geo_region_in_popup_chosen"]').click()
        driver.implicitly_wait(10)
        drp_select_city = driver.find_element(By.XPATH, '//li[@data-option-array-index="1"]').click()
        driver.implicitly_wait(10)
        tab_research = driver.find_element(By.XPATH, '//a[@data-tab="research"]').click()
        driver.implicitly_wait(10)
        name_header = driver.find_element(By.XPATH, '//div[@class="tabs-pane active"]//div[@class="analizes-list-table-header"]//div[@class="analizes-list-table-cell altc-name"]').text
        price_header = driver.find_element(By.XPATH, '//div[@class="tabs-pane active"]//div[@class="analizes-list-table-header"]//div[@class="analizes-list-table-cell altc-price"]').text
        time_header = driver.find_element(By.XPATH, '//div[@class="tabs-pane active"]//div[@class="analizes-list-table-header"]//div[@class="analizes-list-table-cell altc-time"]').text
        name_products = driver.find_elements(By.XPATH, '//div[contains(@class,"analizes-list-table-line tab-line-")]')
        driver.implicitly_wait(10)
        with open(f"C:\\scrap_tutorial-master\\dila_ua\\analysis.csv", "w", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    name_header,
                    price_header,
                    time_header
                )
            )

        for i in name_products:
            name_analysis = i.find_element(By.XPATH,
                                           '//div[@class="tabs-pane active"]//div[contains(@class, "analizes-list-table-line tab-line-")]//div[@class="analizes-list-table-cell altc-name"]').text
            price_analysis = i.find_element(By.XPATH,
                                            '//div[@class="tabs-pane active"]//div[contains(@class, "analizes-list-table-line tab-line-")]//div[@class="analizes-list-table-cell altc-price"]').text
            time_analysis = i.find_element(By.XPATH,
                                           '//div[@class="tabs-pane active"]//div[contains(@class, "analizes-list-table-line tab-line-")]//div[@class="analizes-list-table-cell altc-time"]').text
            print(name_analysis, price_analysis, time_analysis)

            with open(f"C:\\scrap_tutorial-master\\dila_ua\\analysis.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow(
                    (
                        name_analysis,
                        price_analysis,
                        time_analysis
                    )
                )



        # # Листать по страницам ---------------------------------------------------------------------------
        # page_product = 0
        # isNextDisable = False
        # while not isNextDisable:
        #     try:
        #         for i in name_products:
        #             name_analysis = i.find_element(By.XPATH,
        #                                            '//div[@class="tabs-pane active"]//div[contains(@class, "analizes-list-table-line tab-line-")]//div[@class="analizes-list-table-cell altc-name"]').text
        #             price_analysis = i.find_element(By.XPATH,
        #                                             '//div[@class="tabs-pane active"]//div[contains(@class, "analizes-list-table-line tab-line-")]//div[@class="analizes-list-table-cell altc-price"]').text
        #             time_analysis = i.find_element(By.XPATH,
        #                                            '//div[@class="tabs-pane active"]//div[contains(@class, "analizes-list-table-line tab-line-")]//div[@class="analizes-list-table-cell altc-time"]').text
        #             print(name_analysis, price_analysis, time_analysis)
        #
        #             with open(f"C:\\scrap_tutorial-master\\dila_ua\\analysis.csv", "a", errors='ignore') as file:
        #                 writer = csv.writer(file, delimiter=";", lineterminator="\r")
        #                 writer.writerow(
        #                     (
        #                         name_analysis,
        #                         price_analysis,
        #                         time_analysis
        #                     )
        #                 )
        #         next_button = driver.find_element(By.XPATH, '//div[@class="tabs-pane active"]//li[@class="next"]')
        #         # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!
        #         if next_button[0:1]:
        #             next_button.click()
        #             page_product += 1
        #             print(f"Обработано {page_product} страниц")
        #         else:
        #             isNextDisable = True
        #     except:
        #         isNextDisable = True
        # # Листать по страницам ---------------------------------------------------------------------------


        diff_time = datetime.datetime.now() - start_time
    except Exception as ex:
        print(ex)

    finally:
        print(diff_time)
        driver.close()
        driver.quit()


def parse_content():
    url = "https://dila.ua/price.html"
    get_content(url)


if __name__ == '__main__':
    parse_content()
