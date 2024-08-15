import requests
import json
from configuration.logger_setup import logger

cookies = {
    "PHPSESSID": "61d10f9937ace73e3c3970f2b80e4608",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "cache-control": "no-cache",
    # 'cookie': 'PHPSESSID=61d10f9937ace73e3c3970f2b80e4608',
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "referer": "https://twojaoferta.com.pl/",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
}


def get_html():
    response = requests.get(
        "https://twojaoferta.com.pl/ogloszenia", cookies=cookies, headers=headers
    )

    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open("proba.html", "w", encoding="utf-8") as file:
            file.write(response.text)
    print(response.status_code)


def get_json():
    params = {
        "page": "1",
        "firstParam": "namestaj",
        "group": "cipelarnici-i-predsoblja",
        "categoryId": "1268",
        "groupId": "399",
    }

    response = requests.get(
        "https://www.kupujemprodajem.com/api/web/v1/search",
        params=params,
        cookies=cookies,
        headers=headers,
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
    save_path = "image_sitemap_00006.xml"
    url = "https://zorrov.com/image_sitemap_00006.xml"
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


if __name__ == "__main__":
    # get_html()
    # get_json()
    download_xml()
