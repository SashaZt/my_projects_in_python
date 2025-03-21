import json
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from loguru import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"
output_html_file = html_directory / "output.html"


logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)

cookies = {
    "PHPSESSID": "10kivbhe6ol1mkhha9pdaodbb4",
    "abityshopselector_geo_country": "UA",
    "apc_popup_session": "1",
    "twk_idm_key": "EiZhGCE5foTYtwqjdVPFh",
    "cookiesplus": "%7B%22C_P_DISPLAY_MODAL%22%3Afalse%2C%22cookiesplus-finality-6%22%3A%22on%22%2C%22cookiesplus-finality-7%22%3A%22on%22%2C%22cookiesplus-finality-8%22%3A%22on%22%2C%22consent_date%22%3A%222025-03-17%2011%3A15%22%7D",
    "__stripe_mid": "af97732e-a7f6-420e-a3d4-3a3b3486b6ca4767fc",
    "__stripe_sid": "1358719d-9366-4628-8f10-b1bc0f8316e0a94761",
    "TawkConnectionTime": "0",
    "PrestaShop-10837ce59526231749370d049cc2a7ec": "def502004107043e65d22ce7323c91408eb35cca3dd9f444c2e254ac50f09b255dbb7ec7fd02676beebe54b51e082434bf262e86a13ed9f1fd4dfe7386da2f26a290d2bb45495df7f942d7d026af2f314c600446ca877a5296df158282522115e2f703e1e4c8f2067e8ed0bdf616ecd0f9f73d39f56e58fe46c6d6fefe2b848f1188470d151508cff0df9cdc4babb7a07baeb74821048b5e17997f6fd51e00ef3fb472990c0c4b2d9362ac638ce30ee573a267021ba2dd77932d3c861d1243d89c0964b135d1a0157420c185668da10776ba1f8210a25576979acbcd151dfddad8eaa9eef6ceabf85b21c37f48a68ccbc0cec37902c379f0908b1db87fee1358c8cf450a5c9cd7db61fa53698eea93c6c1e36f8ba62f7df29211d733f1b9696849bc30b0107e6688d1f857fce54f19f7f3bc16bd64aad615be493ee639def95af71c54cc02e09dd08173c2ea4884c38e3ff1ae44e4a0fcb1d266f67e7c143ff50410b1350d0cc5ee63c7448cd0f054cf4d9425055d328d",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "referer": "https://www.elinapilates.com/eu/en/59-pilates-reformers",
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


def get_html():

    response = requests.get(
        "https://www.elinapilates.com/eu/en/reformers-with-tower-for-pilates/814-1074-elite-wood-reformer-with-tower.html",
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
    # Находим все элементы <figure> с классом "$relative"
    figures = soup.find_all("figure", class_="$relative")

    # Список для хранения результатов
    results = []

    # Проходим по всем найденным <figure>
    for figure in figures:
        # Ищем <img> внутри каждого <figure>
        img = figure.find("img")
        if img:
            # Извлекаем атрибуты alt и src
            alt_text = img.get("alt", "")  # Если alt отсутствует, вернем пустую строку
            src_url = img.get("src", "")  # Если src отсутствует, вернем пустую строку
            results.append({"alt": alt_text, "src": src_url})

    # Выводим результаты
    for result in results:
        print(f"Alt: {result['alt']}")
        print(f"Src: {result['src']}")
        print("---")

    # Если нужно сохранить в список словарей или файл, вот пример:

    with open("image_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


def get_json():
    cookies = {
        "PHPSESSID": "10kivbhe6ol1mkhha9pdaodbb4",
        "abityshopselector_geo_country": "UA",
        "twk_idm_key": "EiZhGCE5foTYtwqjdVPFh",
        "__stripe_mid": "af97732e-a7f6-420e-a3d4-3a3b3486b6ca4767fc",
        "__stripe_sid": "bef889a9-bf44-4d10-abf0-c64ea62520dd5c62b3",
        "cookieyes-consent": "consentid:QkNxNGVDa2hMT1pXaUhLZVo4c2tGV0NEWTNhYVRFelM,consent:no,action:,necessary:yes,functional:no,analytics:no,performance:no,advertisement:no,other:no",
        "PrestaShop-10837ce59526231749370d049cc2a7ec": "def50200266a245bdbfe1ede788b53264231fc1dc255f6bd12919038be571ce3fdbb600d18bc444cc36119e7e4d9411e5469ea4fbaf6d4098829da6b1ac20b27f2c10dfeea1e6cf5ebdd883dd9eb119fdb0c50fc34b4eecb2673f671af32bb51875b38875065a0241d64e7e9b01a44ea542ed2c9ca8daf6d8098e54d86b0419e49d68da2cabe2fad0dd0201859e1ce75c37f119daeac0067804e69137a45e9786c3348bf2204d869a80fe2bd0b4f3f137efc9ec0d1b71bfd1568d2ac6c7ae67452266ab34e5e4bb92a85e438eebd893fc23591e74abcf34a5b22115178ad0b63d1538a419e24ee9741e4d1541887cb572ab53068af6e287da6b351b93415376f1b25f4b8699824da3664df43508fc57e78a65ee25fda5cb3902906880c80e60af6fe5fd93b2e2fc64fed1bb4ab00cb7cecede8380e23107f8da432ab5eab0c1fbb5fba1cb158b55febdfd0443f714764c2986d7444ea872ace5d2e157bab124ce947e7488843a607dfdb8a5161c34ec8c73b9f56a34e0320d783ee4e1468a23211d565eea0f2ddee00ba61ddaec089e74d28bd8a25c47cac52c084d5658f77b49e983ba909c7257179a25f1c40ab3e589dc2293bbe0058db2a5c033a1977207c97ead10f478d4bb05dc32671cc3d34978600c715b1eda60aa58c9263e0e150cd913acdd04dac2d5af4ae5720af86fdb1f80b960648f471d53ea0ab40ee5a20e0117af75a35897df74bb6931082f08943405769808eb764aae0a5f865c4c20a85e7c721fb1e2cda363bf0615e69f7a7272d2497f9c59881a5a14c91c588c4f3c497779d43a57f5ee93af9a06c83663aca65fd2f6f3a485671608d5728824e98d3e9bffc5fd11a8262d8e03520c96da7096cfb60a9a6c7b9645cd721e392",
        "twk_uuid_5c45d695ab5284048d0ddcfc": "%7B%22uuid%22%3A%221.2BiywJHayPNISef1QfYwKUOuVFlr4HCa33qZsLrj7RNi81VckuBF9vKXSoPMWQNzSB1QiL074YUuvOkWkUbh25cJgzzC5qHOTnHsLp7490rea2UHAZi8UOmICoP%22%2C%22version%22%3A3%2C%22domain%22%3A%22elinapilates.com%22%2C%22ts%22%3A1742554152095%7D",
        "TawkConnectionTime": "1742554162709",
    }

    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "dnt": "1",
        "origin": "https://www.elinapilates.com",
        "priority": "u=1, i",
        "referer": "https://www.elinapilates.com/eu/en/pilates-reformers/1329-2880-nubium-reformer.html",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    params = {
        "controller": "product",
        "token": "bf13ea70c0a5fe1095aea0e0c9153f08",
        "id_product": "1329",
        "id_customization": "0",
        "group[7]": "108",
        "qty": "1",
    }

    data = {
        "quickview": "0",
        "ajax": "1",
        "action": "refresh",
        "quantity_wanted": "1",
    }

    response = requests.post(
        "https://www.elinapilates.com/eu/en/index.php",
        params=params,
        cookies=cookies,
        headers=headers,
        data=data,
        timeout=30,
    )
    file_name = data_directory / f"elinapilates.json"
    try:
        data = response.json()
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)  # Записываем в файл
    except ValueError:
        print("Ошибка: ответ не содержит JSON")


if __name__ == "__main__":
    # get_html()
    get_json()
    # scrap_html()
