import os
import csv
import lxml
import time
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


def clean(text):
    return text.replace('\t', '').replace('\n', '').strip()


def get_content(url):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/107.0.0.0 Safari/537.36 "
    }

    resp = requests.get(url, headers=header)

    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'lxml')
        table = soup.find('div', attrs={'class': 'css-pband8'})
        table_list = table.find_all('div', attrs={'data-cy': 'l-card'})
        url_list = []
        with open("data/oby.csv", "w") as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    "Дата публикации",
                    "Название обьевления",
                    "Цена обьекта",
                    "Описание обьекта",
                    "Телефон",
                    "Имя",
                    "Ссылка"
                )
            )
        for item in table_list:
            href = "https://www.olx.ua" + item.find('a').get("href")
            url_list.append(href)
        oby_data_list = []
        for href in url_list[1:2]:

            req = requests.get(href, headers=header)

            soup = BeautifulSoup(req.text, "lxml")
            data_oby = soup.find('span', class_="css-19yf5ek").text
            name_oby = soup.find('h1', class_="css-r9zjja-Text eu5v0x0").text
            price_oby = soup.find('h3', class_="css-okktvh-Text eu5v0x0").text
            desc_oby = soup.find('div', class_='css-g5mtbi-Text').text.replace("\n", ", ")
            driver.get(f"{href}")
            driver.implicitly_wait(5)

            for cookie in pickle.load(open(f"{olx_email}_cookies", "rb")):
                driver.add_cookie(cookie)
            # driver.implicitly_wait(5)
            driver.refresh()
            time.sleep(randint(1, 5))
            # driver.implicitly_wait(5)
            try:
                # Открывваем кнопку "Показать телефон"
                phone_show = driver.find_element(By.XPATH, '//button[@class="css-65ydbw-BaseStyles"]')
                # driver.implicitly_wait(5)
                driver.implicitly_wait(randint(1, 10))
                time.sleep(randint(1, 10))
                phone_show.click()
                driver.implicitly_wait(randint(1, 10))
                # driver.implicitly_wait(5)
                # Получаем телефон продавца
                contact_phone = driver.find_element(By.XPATH, '//a[@data-testid="contact-phone"]').text
                driver.implicitly_wait(5)
                # driver.implicitly_wait(5)
                contact_name = driver.find_element(By.XPATH, '//h4[@class="css-1rbjef7-Text eu5v0x0"]').text
                with open("data/oby.csv", "a", errors='ignore') as file:
                    writer = csv.writer(file, delimiter=";",
                                        lineterminator="\r")  # lineterminator="\r". Это разделитель между строками таблицы, delimiter Устанавливает символ, с помощью которого разделяются элементы в файле
                    writer.writerow(
                        (
                            data_oby,
                            name_oby,
                            price_oby,
                            desc_oby,
                            contact_phone,
                            contact_name,
                            href
                        )
                    )
            except Exception as ex:
                print(ex)
            finally:
                print("Получили номер телефона")





            # temp = {'title': name, 'adress': adress, 'price_str': price_str, 'price': price, 'url': href}

    # with open("data/olx.html", "w", encoding='utf-8') as file:
    #     file.write(resp.text)


def parse_content():
    url = "https://www.olx.ua/d/uk/nedvizhimost/kvartiry/prodazha-kvartir/zhitomir/?currency=USD&search%5Bfilter_enum_number_of_rooms_string%5D%5B0%5D=dvuhkomnatnye&search%5Bfilter_enum_apartments_object_type%5D%5B0%5D=secondary_market"
    get_content(url)


def parse_content_all():
    url_1 = "https://www.olx.ua/d/uk/nedvizhimost/kvartiry/prodazha-kvartir/zhitomir/?currency=USD&search%5Bfilter_enum_number_of_rooms_string%5D%5B0%5D=dvuhkomnatnye&search%5Bfilter_enum_apartments_object_type%5D%5B0%5D=secondary_market"
    url = "https://www.olx.ua/d/uk/nedvizhimost/kvartiry/prodazha-kvartir/zhitomir/?currency=USD&search%5Bfilter_enum_number_of_rooms_string%5D%5B0%5D=dvuhkomnatnye&search%5Bfilter_enum_apartments_object_type%5D%5B0%5D=secondary_market&page={}"

    url_list = []
    for item in range(2, 3):
        if item > 1:
            _url = url.format(item)
            url_list += get_content(_url)
    print(url_list)
    #     print(f"Станица № {item}")
    #     time.sleep(5)
    # csv_title = ['title', 'adress', 'price_str', 'price', 'url']
    # with open('data/olx.csv', "w") as file:
    #     writer = csv.DictWriter(file, fieldnames=csv_title, delimiter=';')
    #     writer.writeheader()
    #     writer.writerows(ad)


#################TEMP#########################
# name = href.split("/")[-1]
# if os.path.exists(f"data/{name}"):
#     print(f'Файл уже существует {name}.html')
# else:
#     with open(f"data/{name}", "w", encoding='utf-8') as file:
#         file.write(req.text)
# with open(f"data/{name}", encoding='utf-8') as file:
#     src = file.read()
# name = item.find('h6').text
# adress = item.find('p', attrs={'data-testid': 'location-date'}).text
# price_str = item.find('p', attrs={'data-testid': 'ad-price'}).text.replace('Договірна', '')
# price = int(''.join(c for c in price_str if c.isdigit()))
# href = "https://www.olx.ua" + item.a['href']
################################################


if __name__ == '__main__':
    parse_content()
