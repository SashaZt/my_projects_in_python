import requests
import json
import aiohttp
import asyncio
import ssl
import requests
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from configuration.logger_setup import logger
import random
from bs4 import BeautifulSoup


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "1000 ip.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_html():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    cookies = {
        "localization": "FR",
        "secure_customer_sig": "",
        "cart_currency": "EUR",
        "_tracking_consent": "%7B%22con%22%3A%7B%22CMP%22%3A%7B%22a%22%3A%22%22%2C%22m%22%3A%22%22%2C%22p%22%3A%22%22%2C%22s%22%3A%22%22%7D%7D%2C%22v%22%3A%222.1%22%2C%22region%22%3A%22UA18%22%2C%22reg%22%3A%22%22%7D",
        "_cmp_a": "%7B%22purposes%22%3A%7B%22a%22%3Atrue%2C%22p%22%3Atrue%2C%22m%22%3Atrue%2C%22t%22%3Atrue%7D%2C%22display_banner%22%3Afalse%2C%22sale_of_data_region%22%3Afalse%7D",
        "_shopify_y": "0de4acbd-dbfb-4736-a5eb-3bc3f6a461d7",
        "_orig_referrer": "https%3A%2F%2Ffreelancehunt.com%2F",
        "_landing_page": "%2Fen%2Fproducts%2Fbacchantes-small-vase-2",
        "receive-cookie-deprecation": "1",
        "_shopify_sa_p": "",
        "shopify_pay_redirect": "pending",
        "_rsession": "3c51fa43344065a1",
        "_ruid": "eyJ1dWlkIjoiZDRlNzAyNDYtOTcxZC00NDc2LTk3NDItYTlmZTFlY2I0YzE2In0%3D",
        "OptanonAlertBoxClosed": "2024-09-20T04:56:57.235Z",
        "localization": "FR",
        "keep_alive": "82493466-2c7e-4915-8a8f-ddd9296408bb",
        "_shopify_s": "fb17e582-597c-4055-a961-bc734bead7cb",
        "_shopify_sa_t": "2024-09-20T05%3A02%3A54.512Z",
        "OptanonConsent": "isGpcEnabled=0&datestamp=Fri+Sep+20+2024+08%3A02%3A54+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202405.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=cf86adcf-fdfd-4e2a-b6d0-35d763ce64c9&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1%2CC0005%3A1&intType=1&geolocation=UA%3B18&AwaitingReconsent=false",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        # 'cookie': 'localization=FR; secure_customer_sig=; cart_currency=EUR; _tracking_consent=%7B%22con%22%3A%7B%22CMP%22%3A%7B%22a%22%3A%22%22%2C%22m%22%3A%22%22%2C%22p%22%3A%22%22%2C%22s%22%3A%22%22%7D%7D%2C%22v%22%3A%222.1%22%2C%22region%22%3A%22UA18%22%2C%22reg%22%3A%22%22%7D; _cmp_a=%7B%22purposes%22%3A%7B%22a%22%3Atrue%2C%22p%22%3Atrue%2C%22m%22%3Atrue%2C%22t%22%3Atrue%7D%2C%22display_banner%22%3Afalse%2C%22sale_of_data_region%22%3Afalse%7D; _shopify_y=0de4acbd-dbfb-4736-a5eb-3bc3f6a461d7; _orig_referrer=https%3A%2F%2Ffreelancehunt.com%2F; _landing_page=%2Fen%2Fproducts%2Fbacchantes-small-vase-2; receive-cookie-deprecation=1; _shopify_sa_p=; shopify_pay_redirect=pending; _rsession=3c51fa43344065a1; _ruid=eyJ1dWlkIjoiZDRlNzAyNDYtOTcxZC00NDc2LTk3NDItYTlmZTFlY2I0YzE2In0%3D; OptanonAlertBoxClosed=2024-09-20T04:56:57.235Z; localization=FR; keep_alive=82493466-2c7e-4915-8a8f-ddd9296408bb; _shopify_s=fb17e582-597c-4055-a961-bc734bead7cb; _shopify_sa_t=2024-09-20T05%3A02%3A54.512Z; OptanonConsent=isGpcEnabled=0&datestamp=Fri+Sep+20+2024+08%3A02%3A54+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202405.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=cf86adcf-fdfd-4e2a-b6d0-35d763ce64c9&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1%2CC0005%3A1&intType=1&geolocation=UA%3B18&AwaitingReconsent=false',
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://freelancehunt.com/",
        "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://fr.lalique.com/en/products/bacchantes-small-vase-2",
        cookies=cookies,
        headers=headers,
    )

    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open("proba.html", "w", encoding="utf-8") as file:
            file.write(response.text)
    print(response.status_code)


def get_json():
    response = requests.get(
        "https://b.abw.by/api/v2/adverts/1/phones", cookies=cookies, headers=headers
    )

    # Проверка кода ответа
    if response.status_code == 200:
        json_data = response.json()
        # filename = os.path.join(json_path, f"0.json")
        with open("proba.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
    else:
        print(response.status_code)


def download_xml():
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    }
    save_path = "sitemap.products.xml.gz"
    url = "https://www.xos.ro/sitemap.products.xml.gz"
    # Отправка GET-запроса на указанный URL
    response = requests.get(url, headers=headers)

    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Файл успешно сохранен в: {save_path}")
    else:
        print(f"Ошибка при скачивании файла: {response.status_code}")


def parsing():
    with open("proba.html", encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")
    page_title = soup.select_one(
        "#ProductInfo-template--19203350364488__main > div.product__title-inner > div.product__title > h1"
    ).text
    page_title_h3 = soup.select_one(
        "#ProductInfo-template--19203350364488__main > div.product__subtitle > h3"
    ).text
    # description = soup.select_one(
    #     "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(3) > div > div > div > div > div:nth-child(1) > div"
    # ).text.replace("Description", "")
    price = soup.select_one(
        "#price-template--19203350364488__main > div > div > div.price__regular > span.price-item.price-item--regular"
    ).text.strip()
    all_product_info = soup.select_one("#ProductAccordion-product_information > ul")
    info_01 = all_product_info.select_one("li:nth-child(1)").text.strip()
    # Второй элемент — Dimensions
    info_02 = all_product_info.find(
        "li", string=lambda text: "Dimensions" in text
    ).text.strip()

    # Третий элемент — Weight
    info_03 = all_product_info.find(
        "li", string=lambda text: "Weight" in text
    ).text.strip()

    # Четвертый элемент — Handcrafted
    info_04 = all_product_info.find(
        "li", string=lambda text: "Handcrafted" in text
    ).text.strip()
    fotos = soup.find_all(
        "div", attrs=("class", "product__media media media--transparent")
    )
    for foto in fotos:
        img_tag = foto.find("img")
        if img_tag:
            src = img_tag.get("src")
            # Обрезаем строку по символу '?'
            clean_src = src.split("?")[0]
            clean_src = f"https:{clean_src}"
            logger.info(clean_src)

    # sku_item_n = soup.select_one(
    #     "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(2) > div"
    # ).text.replace("Item No.", "")
    # upc = soup.select_one(
    #     "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(4) > div > span:nth-child(2)"
    # ).text
    # brand = soup.select_one(
    #     "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(3) > div > span:nth-child(2)"
    # ).text

    # logger.info(info_02)


if __name__ == "__main__":
    # get_html()
    parsing()
    # get_json()
    # download_xml()
    # fetch_and_save()
