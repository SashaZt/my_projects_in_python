import os
from multiprocessing import Pool
import csv
import lxml
import time
# Нажатие клавиш
from selenium.webdriver.common.keys import Keys
from random import randint
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import csv
from selenium import webdriver
import pickle
from aut_data import olx_pass, olx_email

# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = webdriver.ChromeOptions()
# Отключение режима WebDriver
options.add_experimental_option('useAutomationExtension', False)
options.add_argument(
    "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
)
driver_service = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
driver = webdriver.Chrome(
    service=driver_service,
    options=options
)
# Окно браузера на весь экран
driver.maximize_window()


# def clean(text):
#     return text.replace('\t', '').replace('\n', '').strip()


def get_content(url):
    with open("genel.csv", "w") as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                "Ссылка",
                "Просмотры",
                "Город"
            )
        )
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/107.0.0.0 Safari/537.36 "
    }
    try:
        for item in range(1, 26):
            if item == 1:
                resp = requests.get(url, headers=header)
            elif item > 1:
                resp = requests.get(url + f'&page={item}', headers=header)
            soup = BeautifulSoup(resp.text, 'lxml')
            table = soup.find('div', attrs={'class': 'css-pband8'})
            table_list = table.find_all('div', attrs={'data-cy': 'l-card'})
            url_list = []

            for item in table_list:
                href = "https://www.olx.ua" + item.find('a').get("href")
                url_list.append(href)
            oby_data_list = []
            for href in url_list:

                # req = requests.get(href, headers=header)
                driver.get(f"{href}")
                # time.sleep(30)
                # pickle.dump(driver.get_cookies(), open("cookies", "wb"))
                for cookie in pickle.load(open('cookies', "rb")):
                    driver.add_cookie(cookie)
                driver.implicitly_wait(5)
                driver.refresh()
                time.sleep(10)
                soup = BeautifulSoup(driver.page_source, 'lxml')
                views = soup.find('span', attrs={'data-testid': 'page-view-text'}).text.replace('Переглядів: ', '')
                city = soup.find('p', attrs={'class': 'css-7xdcwc-Text eu5v0x0'}).text
                with open("genel.csv", "a", errors='ignore') as file:
                    writer = csv.writer(file, delimiter=";",
                                        lineterminator="\r")  # lineterminator="\r". Это разделитель между строками таблицы, delimiter Устанавливает символ, с помощью которого разделяются элементы в файле
                    writer.writerow(
                        (
                            href,
                            views,
                            city
                        )
                    )

    except Exception as ex:
        print(ex)

    finally:
        driver.close()
        driver.quit()


def parse_content():
    url = "https://www.olx.ua/d/uk/dom-i-sad/instrumenty/q-%D0%B3%D0%B5%D0%BD%D0%B5%D1%80%D0%B0%D1%82%D0%BE%D1%80/?currency=UAH&search%5Bprivate_business%5D=business&search%5Bfilter_float_price:from%5D=20000&search%5Bfilter_float_price:to%5D=30000"
    get_content(url)

if __name__ == '__main__':
    parse_content()
