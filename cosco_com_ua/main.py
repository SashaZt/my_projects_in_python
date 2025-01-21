import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
import requests
from configuration.logger_setup import logger
import json
import random
from bs4 import BeautifulSoup

# Указываем пути к файлам и папкам
current_directory = Path.cwd()
configuration_directory = current_directory / "configuration"

xlsx_files = current_directory / "xlsx"
html_files = current_directory / "html_files"
xlsx_files.mkdir(parents=True, exist_ok=True)
html_files.mkdir(parents=True, exist_ok=True)
txt_file_proxies = configuration_directory / "roman.txt"
urls_csv = current_directory / "urls.csv"

def load_proxies():
    """Загружает список прокси-серверов из файла."""
    with open(txt_file_proxies, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_xml():

    cookies = {
        'prodex24cur_domain': 'cosco.com.ua',
        'sbjs_migrations': '1418474375998%3D1',
        'sbjs_current_add': 'fd%3D2025-01-13%2016%3A59%3A38%7C%7C%7Cep%3Dhttps%3A%2F%2Fcosco.com.ua%2F%7C%7C%7Crf%3D%28none%29',
        'sbjs_first_add': 'fd%3D2025-01-13%2016%3A59%3A38%7C%7C%7Cep%3Dhttps%3A%2F%2Fcosco.com.ua%2F%7C%7C%7Crf%3D%28none%29',
        'sbjs_current': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
        'sbjs_first': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
        'PHPSESSID': '97dfd5ded6da45a1a23f2ee111e483f8',
        'custom_top_bar_closed': '1',
        'sbjs_udata': 'vst%3D2%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F131.0.0.0%20Safari%2F537.36',
        'sbjs_session': 'pgs%3D6%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fcosco.com.ua%2Fpenal-shhenyachyj-patrul-stakanchyk-zubna-shhitka-zubna-pasta%2F',
        'woodmart_recently_viewed_products': '8870|8230|26625|23828|8580',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru,en;q=0.9,uk;q=0.8',
        'cache-control': 'no-cache',
        # 'cookie': 'prodex24cur_domain=cosco.com.ua; sbjs_migrations=1418474375998%3D1; sbjs_current_add=fd%3D2025-01-13%2016%3A59%3A38%7C%7C%7Cep%3Dhttps%3A%2F%2Fcosco.com.ua%2F%7C%7C%7Crf%3D%28none%29; sbjs_first_add=fd%3D2025-01-13%2016%3A59%3A38%7C%7C%7Cep%3Dhttps%3A%2F%2Fcosco.com.ua%2F%7C%7C%7Crf%3D%28none%29; sbjs_current=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29; sbjs_first=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29; PHPSESSID=97dfd5ded6da45a1a23f2ee111e483f8; custom_top_bar_closed=1; sbjs_udata=vst%3D2%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F131.0.0.0%20Safari%2F537.36; sbjs_session=pgs%3D6%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fcosco.com.ua%2Fpenal-shhenyachyj-patrul-stakanchyk-zubna-shhitka-zubna-pasta%2F; woodmart_recently_viewed_products=8870|8230|26625|23828|8580',
        'dnt': '1',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'referer': 'https://cosco.com.ua/sitemap_index.xml',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }

    response = requests.get('https://cosco.com.ua/product-sitemap.xml', cookies=cookies, headers=headers, timeout=30)

    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open("sitemap_index.xml", "wb") as file:
            file.write(response.content)
    logger.info(response.status_code)
def parsin_xml():
    # Чтение файла sitemap.xml
    with open("sitemap_index.xml", "r", encoding="utf-8") as file:
        xml_content = file.read()

    # Разбор XML содержимого
    root = ET.fromstring(xml_content)

    # Пространство имен XML, используется для правильного извлечения данных
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # Извлечение всех URL из тегов <loc>
    urls = [url.text.strip() for url in root.findall(".//ns:loc", namespace)]

    # Создание DataFrame с URL
    url_data = pd.DataFrame(urls, columns=["url"])

    # Запись URL в CSV файл
    url_data.to_csv("urls.csv", index=False)

# get_html()
# parsin_xml()
def get_html():
    urls = read_cities_from_csv(urls_csv)
    proxies = load_proxies()
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    for url in urls:
        proxy = random.choice(proxies)  # Выбираем случайный прокси
        proxies_dict = {"http": proxy, "https": proxy}
    
        response = requests.get(
            url,
            headers=headers,
            timeout=30,
            # proxies=proxies_dict
        )
        file_name = html_files / f"{url.split('/')[-2]}.html"
        # Проверка кода ответа
        if file_name.exists():
            continue
        if response.status_code == 200:
            # Сохранение HTML-страницы целиком
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(response.text)
        logger.info(file_name)

def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()

def pars_htmls():
    extracted_data = []

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_files.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(content, "lxml")

        # 1. Извлечь заголовок продукта
        product_title = soup.find(
            "h1", class_="product_title entry-title wd-entities-title"
        )
        product_title_text = product_title.text.strip() if product_title else None

        # 2. Извлечь цену
        price = soup.select_one("p.price span.woocommerce-Price-amount.amount bdi")
        price_text = price.text.strip() if price else None

        # 3. Извлечь информацию о наличии
        stock_info = soup.find("p", class_="stock in-stock wd-style-default")
        stock_text = stock_info.text.strip() if stock_info else None

        # 4. Извлечь описание
        description = soup.find("div", id="tab-description")
        description_text = description.get_text(strip=True) if description else None

        # 5. Извлечь артикул
        sku = soup.select_one("span.sku_wrapper span.sku")
        sku_text = sku.text.strip() if sku else None

        # 6. Извлечь категории (текст в строку через join)
        categories = soup.select('span.posted_in a[rel="tag"]')
        category_texts = (
            ", ".join(category.get_text(strip=True) for category in categories)
            if categories
            else ""
        )

        # 7. Найти все изображения с атрибутом role="presentation" и извлечь src
        script_tag = soup.find(
            "script", {"type": "application/ld+json", "class": "rank-math-schema"}
        )
        images_string = None
        if script_tag:
            # Загрузить JSON из содержимого тега
            data = json.loads(script_tag.string)

            # Инициализировать список для ссылок на изображения
            image_urls = []

            # Проход по массиву @graph
            for item in data.get("@graph", []):
                if "@type" in item and item["@type"] == "Product":
                    images = item.get("image", [])
                    # Если изображения представлены списком
                    if isinstance(images, list):
                        image_urls.extend(img["url"] for img in images if "url" in img)

            # Преобразовать список ссылок в строку, разделенную запятыми
            images_string = ", ".join(image_urls)
        # Сбор данных в список
        extracted_data.append(
            {
                "product_title_text": product_title_text,
                "price_text": price_text,
                "stock_text": stock_text,
                "description_text": description_text,
                "sku_text": sku_text,
                "category_texts": category_texts,
                "images_string": images_string,
            }
        )

    # Создание DataFrame и запись в Excel
    df = pd.DataFrame(extracted_data)
    df.to_excel("feepyf.xlsx", index=False)

if __name__ == "__main__":
    get_html()
    # pars_htmls()