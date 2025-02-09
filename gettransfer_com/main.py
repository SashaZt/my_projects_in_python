import json
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests


def get_json():
    # "pages_count": 2 - нужно еще раз делать запрос
    url = "https://gettransfer.com/api/transfers?page=1&role=carrier&filtering%5Bdate_since%5D=&filtering%5Bdate_till%5D=&filtering%5Bsearch%5D=&filtering%5Boffers%5D=except_my&filtering%5Basap%5D=false&filtering%5Bhidden%5D=false&sorting%5Bfield%5D=created_at&sorting%5Border_by%5D=desc"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "dnt": "1",
        "priority": "u=1, i",
        "referer": "https://gettransfer.com/ru/carrier/",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    }

    cookies = {
        "locale": "ru",
        "cookieAccepted": "true",
        "rack.session": "7d455f84ae005c2474c86e22051d3bfaee8fe06ba0167f1a3ba33ef4f4dc4402",
        "__cf_bm": "e8P75t_2BckmkqYpigehUVsFAXWylW5etrPIe6QCZ1Y-1739101960-1.0.1.1-qj_RXPSW1V2CEt4te54xUD2NLvu8ybqq0fmGQCIbq6_ZlhVMqi4UbR6mQbatex3SpGdYa6jApurIfhNPQm6cl9MEJxUyEz2r7dOXWGmkHAI",
        "cf_clearance": "76y32n_xN8BK4lIbvRGb62IVRdDr9144cwJ3tSgvD_0-1739102877-1.2.1.1-NA56OGB530UOCohbhE5yMOxou_mRjuw24FIVAWr1kjUHLVU91auKGE5siuGokhVqdKKIpb4CJ4hLYxhDlll5vulEgopOOeITVDM29CXarwIyxjpvejRaK03MoUiSjxWsXt56OtR5DY2e1LJdav9NiVN42pDaeSzqEtVwWgkT9D.61bW0Y74IN0ZRGE4If0DuNRnzumx8yyYIw68RfLFLucKFOQoYZSIP12y7EeGHahQhv5AGvNEDv39iDuc8QUpeaAJORw1OLZfz_geVcRS1mHiDoRjBta9HcIYeDRzG_1U",
        "io": "n3x-SK4ZPJRc5srKJ7O5",
    }

    try:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))

        response = session.get(url, headers=headers, cookies=cookies, timeout=10)
        response.raise_for_status()
        file_output = "output_json.json"
        with open(file_output, "w", encoding="utf-8") as json_file:
            json.dump(response.json(), json_file, ensure_ascii=False, indent=4)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    except ValueError as json_err:
        print(f"JSON decode error: {json_err}")


def scrap_json():
    # Открытие и загрузка JSON-файла
    with open("output_json.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    all_data = []  # Список для хранения всех обработанных данных
    transfers = data.get("data", {}).get("transfers", [])  # Список трансферов

    for transfer in transfers:
        # Основные данные трансфера
        transfer_id = transfer.get("id", None)  # Уникальный идентификатор трансфера
        duration = transfer.get("duration", None)  # Продолжительность трансфера
        distance = transfer.get("distance", None)  # Расстояние в км
        time = transfer.get("time", None)  # Время в минутах
        transfer_type = transfer.get("type", None)  # Тип трансфера (one_way, round_trip и т.д.)
        pax = transfer.get("pax", None)  # Количество пассажиров
        date_to_local = transfer.get("date_to_local", None)  # Локальная дата и время отправления
        date_end_local = transfer.get("date_end_local:", None)  # Локальная дата и время отправления
        date_return_local = transfer.get("date_return_local", None)  # Локальная дата и время отправления
        
        # Данные о месте отправления
        from_data = transfer.get("from", {})
        from_location = from_data.get("name", None)  # Название места отправления
        from_point = from_data.get("point", None)  # Координаты места отправления
        from_country = from_data.get("country", None)  # Страна отправления
        from_types = from_data.get("types", None)  # Страна отправления

        # Данные о месте назначения
        to_data = transfer.get("to", {}) or {}
        to_location = to_data.get("name", None)  # Название места назначения
        to_point = to_data.get("point", None)  # Координаты места назначения
        to_country = to_data.get("country", None)  # Страна назначения
        to_types = to_data.get("types", None)  # Страна назначения

        # Доп.параметры
        transport_type_ids = transfer.get("transport_type_ids", [])  # Типы транспорта


        # Финансовая и статусная информация
        created_at = transfer.get("created_at", None)  # Дата и время создания
        no_competitors = transfer.get("no_competitors", None)  # Есть ли конкуренты на этот трансфер.
        carrier_offer = transfer.get("carrier_offer", None)  # Предложение перевозчика (если есть).
        status = transfer.get("status", None)  # Статус трансфера (new и т.д.)
        comment = transfer.get("comment", "")  # Комментарий к трансферу
        suggested_prices = transfer.get("suggested_prices", {})
        urgent = transfer.get("urgent", None) #Является ли трансфер срочным.
        prices_output = [
            {"type": key.capitalize(), "amount": value.get("amount", None)}
            for key, value in suggested_prices.items()
        ]

        # Дополнительные поля
        
        asap = transfer.get("asap", False)  # Срочность трансфера
        commission = transfer.get("commission", 0.0)  # Комиссия
        uuid = transfer.get("uuid", None)  # Уникальный UUID трансфера
        
        offerable_for = transfer.get("offerable_for", 0)  # Время для предложения

        # Формирование итогового словаря для одного трансфера
        json_data = {
            
            "transfer_id": transfer_id,
            "duration": duration,
            "distance": distance,
            "time": time,
            "type": transfer_type,
            "transport_type_ids": transport_type_ids,
            "pax": pax,
            "date_to_local": date_to_local,
            "date_end_local": date_end_local,
            "date_return_local": date_return_local,
            "from_location": from_location,
            "from_point": from_point,
            "from_country": from_country,
            "from_types": from_types,
            "to_location": to_location,
            "to_point": to_point,
            "to_country": to_country,
            "to_types": to_types,
            "prices_output": prices_output,
            "status": status,
            "asap": asap,
            "commission": commission,
            "uuid": uuid,
            "comment": comment,
            "offerable_for": offerable_for,
            "created_at": created_at,
            "urgent": urgent,
            "no_competitors": no_competitors,
            "carrier_offer": carrier_offer,
        }
        
        all_data.append(json_data)

    # Сохранение итоговых данных в новый JSON-файл
    with open("output.json", "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)





if __name__ == "__main__":
    get_json()
    scrap_json()
