import shutil
import os
import json
import lxml
import requests
import csv
from bs4 import BeautifulSoup


def get_date(url):
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    }

    req = requests.get(url, headers)
    # 2. Сохрняем файл что-бы с ним дальше работать
    with open('karamel.html', 'w', encoding='utf-8') as file:
        file.write(req.text)
    # Открываем файл и все сохраняем в переменную
    with open('karamel.html', encoding='utf-8') as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')

    cofe = soup.find_all('div', class_="l-GwW js-productad")
    cofe_urls = []
    product_list = []
    for item in cofe:
        cofe_url = "https://prom.ua" + item.find('div', class_="M3v0L DUxBc sMgZR _5R9j6 qzGRQ IM66u J5vFR hxTp1").find(
            'a').get("href")
        cofe_name = item.find('span', class_="_3Trjq htldP _7NHpZ h97_n").text
        rep = ['. ', ' ', '\\', '/']
        for i in rep:
            if i in cofe_name:
                cofe_name = cofe_name.replace(i, '_')

        cofe_urls.append(cofe_url)
        if os.path.exists(f"data/{cofe_name}.html"):
            print(f'Файл уже существует {cofe_name}.html')
        else:
            with open(f"data/{cofe_name}.html", "w", encoding='utf-8') as file:
                file.write(req.text)
        with open(f"data/{cofe_name}.html", encoding='utf-8') as file:
            src = file.read()

        try:
            soup = BeautifulSoup(src, "lxml")
            product_name = soup.find('div', class_='MafxA _6xArK WIR6H').find('h1').text
            product_price = soup.find('div', class_='M3v0L -pUjB YKUY6 zG-pk').find('span').text
            product_country = soup.find('ul', class_='nujFR nYCd8').find_all('span')
            product_char = []
            for item in product_country:
                product_char.append(item.text)
            product_list.append(
                (
                    product_name,
                    product_price,
                    product_char
                )
            )

        except Exception as ex:
            print(f'{cofe_name}.html --------------------- ошибка')
    # with open("data/cofe.json", "a", encoding='utf-8') as file:
    #     json.dump(product_list, file, indent=4, ensure_ascii=False)
    # print(product_list)

    # for cofe_in_url in cofe_urls:
    #     req = requests.get(cofe_in_url, headers)

    with open("data/cofe.json", "a", encoding='utf-8') as file:
        json.dump(product_list, file, indent=4, ensure_ascii=False)


get_date('https://prom.ua/c2820375-internet-kofejnya-karamel.html')
