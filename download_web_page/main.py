import requests
import json

cookies = {
    "PHPSESSID": "1mttsq98tsot1rt11rcir6r2gn",
    "default": "fiefijrifks6r5c6stgfn8gok5",
    "currency": "UAH",
    "__ub_cid": "4206b9a5-be4e-41f4-bd08-ce1b8cc74320",
    "__ub_closed_341": "1",
    "ajaxLanguage": "ru-ru",
    "__ub_sid": "6a865f1a-988d-4203-b1c4-618eb6f296af",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "cache-control": "no-cache",
    # 'cookie': 'PHPSESSID=1mttsq98tsot1rt11rcir6r2gn; default=fiefijrifks6r5c6stgfn8gok5; currency=UAH; __ub_cid=4206b9a5-be4e-41f4-bd08-ce1b8cc74320; __ub_closed_341=1; ajaxLanguage=ru-ru; __ub_sid=6a865f1a-988d-4203-b1c4-618eb6f296af',
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
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
    response = requests.get(
        "https://liqui-moly.com.ua/spetsprogrammy/moto/motornye-masla-dlya-mototsiklov/liqui-moly-racing-2t-1l",
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
    get_html()
    # get_json()
