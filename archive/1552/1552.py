import shutil
import os
import json
import lxml
import requests
import csv
from bs4 import BeautifulSoup

# переменная ссылка
url = 'https://1552.com.ua/ru/'
# Заголовки необходимы что бы сайт думал что мы обычный пользователь
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
}
# 1. переменная  reg будет возвращать метода get библиотеки requests, ссылка + заголовки
reg = requests.get(url, headers)
src = reg.text
# 2. Сохрняем файл что-бы с ним дальше работать
with open('1552.html', 'w', encoding='utf-8') as file:
    file.write(src)
# Открываем файл и все сохраняем в переменную
with open('1552.html', encoding='utf-8') as file:
    src = file.read()

soup = BeautifulSoup(src, 'lxml')
for item in range(0, 30):
    all_link_site_01 = soup.find(class_="col_1").find(class_="level_1").find_all("a")
    all_link_site_02 = soup.find(class_="col_2").find(class_="level_1").find_all("a")

    all_link_site = {}
    for item in all_link_site_01:
        item_name = item.text
        item_href = item.get("href")
        # print(f"{item_name}, {item_href}")
        all_link_site[item_name] = item_href
    for item in all_link_site_02:
        item_name = item.text
        item_href = item.get("href")
        # print(f"{item_name}: {item_href}")
        all_link_site[item_name] = item_href
    with open("data/all_link_site.json", 'w') as file:
        json.dump(all_link_site, file, indent=4, ensure_ascii=False)

    # Рабоат с Json файлом
    with open("data/all_link_site.json") as file:
        all_site = json.load(file)

count = 0
for categor_name, categor_href in all_site.items():
    # if count == 5:
    company = []
    rep = [', ', ' ', '-', '/']
    for item in rep:
        if item in categor_name:
            categor_name = categor_name.replace(item, '_')
    rep_ = ['__']
    for item in rep_:
        if item in categor_name:
            categor_name = categor_name.replace(item, '_')

    if os.path.exists(f'data/{categor_name}'):
        print("Папка уже существует")
    else:
        os.mkdir(f'data/{categor_name}')
    req = requests.get(url=categor_href, headers=headers)
    src = req.text
    if os.path.exists(f"data/{categor_name}/{categor_name}.html"):
        print('Файл существует')
    else:
        with open(f"data/{categor_name}/{categor_name}.html", 'w', encoding='utf-8') as file:
            file.write(src)

    with open(f"data/{categor_name}/{categor_name}.html", encoding='utf-8') as file:
        src = file.read()

    soup = BeautifulSoup(src, 'lxml')
    if soup.find_all('div', class_="geodata"):
        for item in soup.find_all('div', class_="geodata"):
            company_name = item.find_next('div', class_="name").text.strip()
            company_add = item.find_next('div', class_="address").text.strip()
            company_tel = item.find_next('div', class_="telefon").text.strip()
            company.append(
                {
                    "Категория:": categor_name,
                    "Название компании": company_name,
                    "Адрес компании": company_add,
                    "Телефон компании": company_tel
                }
            )

        with open(f"data/{categor_name}/company.json", 'a', encoding="utf-8") as file:
            json.dump(company, file, indent=4, ensure_ascii=False)
    else:
        shutil.rmtree(f'data/{categor_name}')
