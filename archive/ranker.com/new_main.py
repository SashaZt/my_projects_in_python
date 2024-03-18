import csv
import re
import time

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
# Нажатие клавиш
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки

useragent = UserAgent()


def get_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()

    if user_agent:
        chrome_options.add_argument(f'--user-agent={user_agent}')

    s = Service(
        executable_path="D:\\Hype data\\ranker.com\\chromedriver.exe"
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )

    return driver


def save_link_all_product(url):
    driver = get_chromedriver(use_proxy=False,
                              user_agent=f"{useragent.random}")
    driver.get(url=url)
    driver.maximize_window()
    time.sleep(1)
    # Выполняется первый цик, как только он закончится сразу переходим к следующему. Подбираем настройку через Debag
    more_ = False
    while not more_:
        try:
            driver.find_element(By.XPATH, '//span[text() = "more"]').click()
            driver.execute_script("window.scrollBy(0,50)", "")
            time.sleep(1)

        except:
            break
    # После выполнения скрипта выполняем сохранение файла. Подбираем настройку через Debag
    next_up = False
    while not next_up:
        try:
            driver.execute_script("window.scrollBy(0,200)", "")
            time.sleep(1)
            button_load_more = driver.find_element(By.XPATH,
                                                   '//button[@class="button_main__b1K6d button_large__mns0w button_secondary__1ZG1U NextList_main__39AJ4"]').click()
            driver.execute_script("window.scrollBy(0,500)", "")

        except:
            break

    with open("data_new.html", "w", encoding='utf-8') as file:
        file.write(driver.page_source)

    print("Скачал страницу")
    driver.close()
    driver.quit()


def get_items(file_path):
    with open(f"data_new.csv", "w", errors='ignore') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                'Name', 'Number', "Info"

            )
        )
    with open(file_path, encoding='utf-8') as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")
    # Таблица где находятся всё карточки
    table = soup.find('ul', attrs={'data-testid': 'list-item-ul'})
    # cart_table = table.find_all('li', attrs={'class': 'listItem_main__'})
    # Найти класс который содержит часть текста BeautifulSoup
    regex_cart = re.compile('blogItem_container.*')
    # Находим все карточки в таблице
    cart_table = table.find_all('li', attrs={'class': regex_cart})
    for i in cart_table:
        name_card = i.find('div', attrs={'class': 'Title_itemNameContainer__tFt8d'}).text
        namber_card = i.find('strong', attrs={'class': 'RankBox_main__QVS8M RankBox_isBlog__g6kiY'}).text
        regex_img = re.compile('Media_main__ex93e.*')
        if i.find('figure', attrs={'class': regex_img}).find('img').get("data-src"):
            img_card = i.find('figure', attrs={'class': regex_img}).find('img').get("data-src").replace(
                "q=60&fit=crop&fm=pjpg&dpr=2&w=650",
                "q=100&fit=crop&fm=pjpg&dpr=2&w=250")
        else:
            img_card = i.find('figure', attrs={'class': regex_img}).find('img').get("src").replace(
                "q=60&fit=crop&fm=pjpg&dpr=2&w=650",
                "q=100&fit=crop&fm=pjpg&dpr=2&w=250")
        # Выкачка фото
        img_data = requests.get(img_card)
        with open(
                f"./img_new/{namber_card}.jpg", 'wb') as file_img:
            file_img.write(img_data.content)
        try:
            albums_card = i.find('div', attrs={'class': 'richText_container__p5dag'}).text.replace("\n", " ")
        except:
            albums_card = "not alboms"

        # try:
        #     Group = albums_card[0].text.replace('Group: ', '')
        # except:
        #     Group = "Not Albums"
        # try:
        #     Labels = albums_card[1].text.replace('Label: ', '')
        # except:
        #     Labels = "Not Labels"
        # try:
        #     Nationality = albums_card[2].text.replace('Nationality: ', '')
        # except:
        #     Nationality = "Not Nationality"
        # try:
        #     Birthdate = albums_card[3].text.replace('Birthdate: ', '')
        # except:
        #     Birthdate = "Not Birthdate"

        with open(f"data_new.csv", "a", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    name_card, namber_card, albums_card

                )
            )


if __name__ == '__main__':
    print("Вставьте ссылку")
    url = 'https://www.ranker.com/list/hot-male-kpop-idols/taylor-park?ref=all_in_one&rlf=GRID'
    save_link_all_product(url)
    get_items('data_new.html')
