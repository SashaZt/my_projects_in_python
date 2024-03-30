import requests
import json
from datetime import datetime, timedelta


def main(c_date):
    cookies = {
        "_gid": "GA1.3.83709849.1711489472",
        "_ga_SX032CTY0J": "GS1.1.1711709816.10.1.1711709816.0.0.0",
        "_ga": "GA1.1.1033939357.1710925091",
        "PHPSESSID": "3rbh4n4i74bp37h6cmlf95q5bi",
    }

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        # 'Cookie': '_gid=GA1.3.83709849.1711489472; _ga_SX032CTY0J=GS1.1.1711709816.10.1.1711709816.0.0.0; _ga=GA1.1.1033939357.1710925091; PHPSESSID=3rbh4n4i74bp37h6cmlf95q5bi',
        "DNT": "1",
        "Origin": "https://www.oree.com.ua",
        "Referer": "https://www.oree.com.ua/index.php/control/results_mo/DAM",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    data = {
        "c_date": c_date,
    }

    response = requests.post(
        "https://www.oree.com.ua/index.php/control/lines_data/",
        cookies=cookies,
        headers=headers,
        data=data,
    )
    json_data = response.json()
    with open(f"rdn.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл

    # Загрузка содержимого JSON файла
    with open(f"rdn.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    # Проход по каждому ключу в "IPS" и удаление ключа "buy"
    for hour in data["IPS"]:
        if "buy" in data["IPS"][hour]:
            del data["IPS"][hour]["buy"]

    # Сохранение изменённого содержимого обратно в файл
    with open(f"rdn.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    date_str = datetime.now()
    delivery_date_str = date_str + timedelta(days=1)
    c_date = delivery_date_str.strftime("%d.%m.%Y")
    main(c_date)
