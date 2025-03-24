import csv
import json
import random
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_xlsx_file = data_directory / "output.xlsx"
output_json_file = data_directory / "output.json"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
output_html_file = html_directory / "eneba.html"
BASE_URL = "https://www.eneba.com/"


def get_html():
    cookies = {
        "userId": "816754927725483513618372764695779",
        "exchange": "UAH",
        "__utmzzses": "1",
        "lng": "en",
        "region": "ukraine",
        "cconsent": "1",
        "scm": "d.ukraine.84d9bb38d29b9d3a.813d5dac64e0d708bd659d768ab13474288332e3f110972be4099e233815ab64",
        "PHPSESSID_": "c4uqne846dcm80l97qqpsb730v",
        "cf_clearance": "Db1h1zgPXGs_xUCJ8cBks8AeKtatt2l310tMqcXu1jM-1742475666-1.2.1.1-YcMRu9rC0oor2fn1r2EuoBKHgDmv2mE1B486QzdxegPKAtWR7y4ERsY8shjFF3muRZy9.ufokIhaH.5Q2o8a.qVWAw6TZAUbZh7hjo80urRYY4ofmyX6o9oI8wvEbfh8ZA1_OFArNQnsZt28MZSNE8Yt.naLOmZqL72MocQpCreT3r96zY_dbu8XW3aBCTzCFEI3HBgpfQsusvexttuq60FhvcoG9tKa7ABpH1awWdkA3BU_DSb6fg.15o4DBpaTAbuIOCsWiByJjpCAubQoYdSI9nDp64UGSuUtYerzKz_KuFZ86HDHAxLP6YRiCnpXDufz4IKr5scfatoPcxuQus52lnk2.awpGpRaLEzkRmo",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://www.eneba.com/store/games?drms[]=xbox&enb_campaign=Homepage&enb_content=Main%20Categories%20Navigation&enb_medium=link&enb_source=https%3A%2F%2Fwww.eneba.com%2F&enb_term=Games&page=1&rangeTo=1000%C2%AEions%5B%5D%3Dargentina%C2%AEions%5B%5D%3Dunited_states%C2%AEions%5B%5D%3Dturkey&regions[]=argentina&regions[]=united_states&regions[]=turkey&sortBy=POPULARITY_DESC&types[]=game",
        cookies=cookies,
        headers=headers,
        timeout=30,
    )

    # Проверка кода ответа
    if response.status_code == 200:

        # Сохранение HTML-страницы целиком
        with open(output_html_file, "w", encoding="utf-8") as file:
            file.write(response.text)
        logger.info(f"Successfully saved {output_html_file}")
    else:
        logger.error(f"Failed to get HTML. Status code: {response.status_code}")


def scrap_html():

    with open(output_html_file, "r", encoding="utf-8") as file:
        content = file.read()
    soup = BeautifulSoup(content, "lxml")
    # Поиск тега script с id="__APOLLO_STATE__"
    apollo_script = soup.find("script", {"id": "__APOLLO_STATE__"})

    if apollo_script:
        # Извлечение JSON-данных из тега script
        apollo_data = apollo_script.string

        # Проверка на пустые данные
        if apollo_data:
            # Преобразование данных в словарь Python
            try:
                data_dict = json.loads(apollo_data)
                # Сохранение данных в JSON-файл
                with open(output_json_file, "w", encoding="utf-8") as out_file:
                    json.dump(data_dict, out_file, ensure_ascii=False, indent=4)
                process_apollo_data(data_dict)
                logger.info(
                    f"Данные Apollo State успешно сохранены в {output_json_file}"
                )
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка декодирования JSON: {e}")
        else:
            logger.error("Тег Apollo State найден, но не содержит данных")
    else:
        logger.error("Тег Apollo State не найден в HTML")


def process_apollo_data(apollo_data):
    """
    Обрабатывает данные Apollo State и формирует список товаров
    в требуемом формате
    """
    result = []

    # Словари для хранения информации об аукционах и продуктах
    auctions = {}
    products = {}

    # Сначала собираем все данные аукционов и продуктов
    for key, value in apollo_data.items():
        if key.startswith("Auction::"):
            auctions[key] = value
        elif key.startswith("Product::"):
            products[key] = value

    # Для каждого продукта находим соответствующий аукцион и формируем запись
    for product_key, product in products.items():
        # Проверяем, есть ли у продукта ссылка на аукцион
        cheapest_auction_ref = product.get("cheapestAuction", {}).get("__ref")

        if not cheapest_auction_ref:
            continue

        # Получаем данные аукциона
        auction = auctions.get(cheapest_auction_ref)
        if not auction:
            continue

        # Получаем цену в UAH и делим на 100
        price_uah = None
        price_data = auction.get('price({"currency":"UAH"})')
        if price_data and "amount" in price_data:
            price_uah_str = str(price_data["amount"] / 100)
            price_uah = price_uah_str.replace(".", ",") if price_uah_str else None

            # Получаем имя продукта и очищаем его от лишней информации
        # Получаем имя продукта и очищаем его от лишней информации
        product_name = product.get("name", "")

        if product_name:
            # Удаляем "XBOX LIVE Key" из названия
            product_name = (
                product_name.replace("XBOX LIVE Key", "")
                .replace("Xbox Live Key", "")
                .strip()
            )

            # Получаем регионы из продукта
            regions = []

            if "regions" in product and isinstance(product["regions"], list):
                for region in product["regions"]:

                    if isinstance(region, dict) and "name" in region:
                        # Добавляем название региона и его вариант в верхнем регистре
                        regions.append(region["name"].upper())

            # Удаляем название региона из конца наименования товара
            for region in regions:
                # Проверяем наличие региона в конце строки (с учетом возможного пробела)
                if product_name.endswith(region):
                    product_name = product_name[: -len(region)].strip()
                elif product_name.endswith(" " + region):
                    product_name = product_name[: -(len(region) + 1)].strip()

        # Получаем slug продукта
        product_slug = product.get("slug", "")

        # Получаем URL изображения
        img_url = ""
        cover_data = product.get('cover({"size":300})')
        if cover_data and "src" in cover_data:
            img_url = cover_data["src"]

        # # Формируем запись
        # item = {
        #     "Цена": price_uah.replace(".", ",") if price_uah else None,
        #     "Название товара": product_name,
        #     "Ссылка на товар": f"{BASE_URL}{product_slug}",
        #     "Ссылка на изображение": img_url,
        # }
        # Формируем запись согласно требуемым заголовкам
        item = {
            "Код_товару": product_name[:24],
            "Назва_позиції": f"{product_name} Код для Xbox One/Series S|X",
            "Назва_позиції_укр": f"{product_name} Код для Xbox One/Series S|X",
            "Пошукові_запити": f"{product_name},Xbox,xbox ігри,xbox game pass ultimate активация,xbox game pass для консолей,подписка xbox game pass пк,xbox game pass ultimate,xbox game pass 1 месяц,xbox game pass ultimate 5 месяцев,xbox game pass ultimate 5 місяців,xbox game pass ultimate 9 місяців,xbox game pass ultimate 25 місяців,xbox game pass ultimate 13 місяців,xbox game pass ultimate 17 місяців,xbox game pass ultimate продление,подписка xbox game pass ultimate 1 месяц,подписка xbox game pass ultimate 5 месяцев,подписка xbox game pass ultimate 9 месяцев,подписка xbox game pass ultimate 24 месяца,подписка xbox game pass ultimate 13 месяцев,подписка xbox game pass ultimate 17 месяцев,підписка xbox game pass ultimate 5 місяців,підписка xbox game pass ultimate 9 місяців,підписка xbox game pass ultimate 24 місяці,підписка xbox game pass ultimate 13 місяців,підписка xbox game pass ultimate 12 місяців,підписка xbox game pass ultimate 17 місяців,",
            "Пошукові_запити_укр": f"{product_name},Xbox,xbox ігри,xbox game pass ultimate активация,xbox game pass для консолей,подписка xbox game pass пк,xbox game pass ultimate,xbox game pass 1 месяц,xbox game pass ultimate 5 месяцев,xbox game pass ultimate 5 місяців,xbox game pass ultimate 9 місяців,xbox game pass ultimate 25 місяців,xbox game pass ultimate 13 місяців,xbox game pass ultimate 17 місяців,xbox game pass ultimate продление,подписка xbox game pass ultimate 1 месяц,подписка xbox game pass ultimate 5 месяцев,подписка xbox game pass ultimate 9 месяцев,подписка xbox game pass ultimate 24 месяца,подписка xbox game pass ultimate 13 месяцев,подписка xbox game pass ultimate 17 месяцев,підписка xbox game pass ultimate 5 місяців,підписка xbox game pass ultimate 9 місяців,підписка xbox game pass ultimate 24 місяці,підписка xbox game pass ultimate 13 місяців,підписка xbox game pass ultimate 12 місяців,підписка xbox game pass ultimate 17 місяців,",
            "Опис": f"<p><strong>Добро пожаловать в наш магазин цифровых товаров &laquo;XGames_Store&raquo; у нас лучшие цены и предложения!!!</strong></p><p><strong>Пожалуйста, внимательно ознакомьтесь с описанием перед покупкой.</strong></p><p><strong>Вы получите лицензионный цифровой код для активации игры {product_name}!</strong></p><p><strong>Доставка осуществляется только по полной предоплате.<br />Доставка цифрового товара через Telegram/Viber/Whatsapp/Email !!!</strong></p><p><strong>Игра активируется навсегда на вашем аккаунте Microsoft !</strong></p><p><strong>Предоставляем инструкцию и помогаем с активацией (Во время активации может понадобиться VPN или изменение региона / страны).<br /><br />В наличии более 1000 игр для консолей XBOX!</strong></p>",
            "Опис_укр": f"<p><strong>Ласкаво просимо до нашого магазину цифрових товарів &quot;XGames_Store&quot; у нас найкращі ціни та пропозиції!!</strong></p><p><strong>Будь ласка, уважно ознайомтесь з описом перед покупкою.</strong></p><p><strong>Ви отримаєте ліцензійний цифровий код для активації гри {product_name}!</strong></p><p><strong>Доставка здійснюється тільки за повною передоплатою.<br />Доставка цифрового товару через Telegram/Viber/Whatsapp/Email !!!</strong></p><p><strong>Гра активується назавжди на вашому акаунті Microsoft !</strong></p><p><strong>Надаємо інструкцію та допомагаємо з активацією (Під час активації може знадобитись VPN або зміна регіону/країни).<br /><br />В наявності більше 1000 ігор для консолей XBOX!</strong></p>",
            "Тип_товару": "r",
            "Ціна": price_uah,
            "Валюта": "UAH",
            "Одиниця_виміру": "шт.",
            "Мінімальний_обсяг_замовлення": "",
            "Оптова_ціна": "",
            "Мінімальне_замовлення_опт": "",
            "Посилання_зображення": img_url,
            "Наявність": "!",
            "Кількість": "",
            "Номер_групи": "129793815",
            "Назва_групи": "Игры для Xbox",
            "Посилання_підрозділу": "https://prom.ua/Video-igry",
            "Можливість_поставки": "",
            "Термін_поставки": "",
            "Спосіб_пакування": "",
            "Спосіб_пакування_укр": "",
            "Унікальний_ідентифікатор": "",
            "Ідентифікатор_товару": "",
            "Ідентифікатор_підрозділу": "180606",
            "Ідентифікатор_групи": "",
            "Виробник": "Microsoft",
            "Країна_виробник": "США",
            "Знижка": "5%",
            "ID_групи_різновидів": "",
            "Особисті_нотатки": "",
            "Продукт_на_сайті": "",
            "Термін_дії_знижки_від": "",
            "Термін_дії_знижки_до": "",
            "Ціна_від": "-",
            "Ярлик": "Топ",
            "HTML_заголовок": "",
            "HTML_заголовок_укр": "",
            "HTML_опис": "",
            "HTML_опис_укр": "",
            "Код_маркування_(GTIN)": "",
            "Номер_пристрою_(MPN)": "",
            "Вага,кг": "",
            "Ширина,см": "",
            "Висота,см": "",
            "Довжина,см": "",
            "Де_знаходиться_товар": "",
            "Назва_Характеристики": "Платформа",
            "Одиниця_виміру_Характеристики": "",
            "Значення_Характеристики": "Xbox Series X",
        }

        result.append(item)
    # Create DataFrame with a single row
    df = pd.DataFrame(result)

    # Save to CSV
    df.to_excel(output_xlsx_file, index=False)
    logger.info(f"Successfully saved {output_xlsx_file}")


if __name__ == "__main__":
    # get_html()
    scrap_html()
