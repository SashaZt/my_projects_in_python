import requests
import json
from configuration.logger_setup import logger

cookies = {
    "welcome_modal": "1",
    "KUPUJEMPRODAJEM": "leki6ck7cm1evg50hobnspuv3i",
    "machine_id": "48b5fbfc16462e5079ad7b11a3ccd56b",
    "cookie_consent_v2": "1",
    "screenWidth": "1009",
    "recentSearchFilterIds": "[4252817651%2C2012335640%2C5192497351%2C4252844831]",
}

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "baggage": "sentry-environment=production,sentry-release=c544575fc2,sentry-public_key=ade3a6d932cd4f6b842b3002359f4e59,sentry-trace_id=dd49b17d5cc949bfa4501e5d38a9ed24",
    # 'cookie': 'welcome_modal=1; KUPUJEMPRODAJEM=leki6ck7cm1evg50hobnspuv3i; machine_id=48b5fbfc16462e5079ad7b11a3ccd56b; cookie_consent_v2=1; screenWidth=1009; recentSearchFilterIds=[4252817651%2C2012335640%2C5192497351%2C4252844831]',
    "dnt": "1",
    "priority": "u=1, i",
    "referer": "https://www.kupujemprodajem.com/namestaj/cipelarnici-i-predsoblja/grupa/1268/399/2?page=2",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sentry-trace": "dd49b17d5cc949bfa4501e5d38a9ed24-bdcacae554983fff-0",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "x-kp-channel": "desktop_react",
    "x-kp-machine-id": "48b5fbfc16462e5079ad7b11a3ccd56b",
    "x-kp-session": "leki6ck7cm1evg50hobnspuv3i",
    "x-kp-signature": "7fecb8cce20c45e4a738b446ecbebf611c7d3350",
}


def get_html():
    response = requests.get(
        "https://motostyle.ua/filtr-maslyaniy-hiflo-hf138rc",
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


if __name__ == "__main__":
    # get_html()
    get_json()
