import os
import time
import lxml
import requests
import csv
import re
import pickle
from selenium import webdriver
from bs4 import BeautifulSoup

import time
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# options = webdriver.ChromeOptions()
# options.add_argument(
#     "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
# )
# driver_service = Service(executable_path="C:\\scrap_tutorial-master\\dila_ua\\chromedriver.exe")
# driver = webdriver.Chrome(
#     service=driver_service,
#     options=options
# )
def get_data_with_selenium(url):
    try:



        # with open("data/synevo.html", 'w', encoding='utf-8') as file:
        #     file.write(driver.page_source)
        with open("data/synevo.html", encoding='utf-8') as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        # print(soup)
        # Собираем заголовки таблицы
        table_head = soup.find(class_="table").find("tr").find_all("th")
        name_table_head = table_head[0].text
        price_table_head = table_head[1].text
        with open("data/synevo.csv", "w", encoding="windows-1251") as file:
            writer = csv.writer(file)
            writer.writerow(
                (
                    name_table_head,
                    price_table_head
                )
            )
        # analiz_name = soup.find("tr", class_=re.findall(r"search__item service\w"))
        analiz = []
        analiz_name = soup.find('table', {'id': 'all_tests_table'})
        tbody = analiz_name.find('tbody')
        for tr in tbody.find_all("td"):
            analiz.append(tr.text)
        print(analiz)








    except Exception as ex:
        print(ex)

    finally:
        print('*' * 20)
        # driver.close()
        # driver.quit()

get_data_with_selenium("https://www.synevo.ua/ua/tests/1")