import json
import random
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from config.logger import logger

current_directory = Path.cwd()
json_directory = current_directory / "json"


cookies = {
    "lang": "ru_RU",
    "PHPSESSID": "203aa3b0ae4a1f79186eaf64e7f98699",
    "login": "evgen.bikermarket%40gmail.com",
    "_identity": "%5B9%2Cnull%2C2592000%5D",
    "_csrf": "OiOzsFvEdP2qiJwa92QM2FRzprtl_Fed",
    "authSubdomain": "bikermarket",
    "userId": "9",
}

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "Referer": "https://bikermarket.salesdrive.me/ru/index.html?formId=1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "X-CSRF-Token": "D9FQq2Jktz0GjjZA-ge9_Z9T96f9H4wpWG1ehBuxWS1AuB_RESLBeGLeBDGTTcqcpmGm6s9Z3lMoHyroRPc8SQ==",
    "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def get_json():
    for page in range(1, 347):
        file_name = json_directory / f"page_{page}.json"
        if file_name.exists():
            continue

        if page == 1:

            params = {
                "formId": "1",
                "mobileMode": "0",
                "mode": "contactList",
            }
        else:
            params = {
                "formId": "1",
                "mobileMode": "0",
                "mode": "contactList",
                "page": page,
            }
        response = requests.get(
            "https://bikermarket.salesdrive.me/contacts/",
            params=params,
            cookies=cookies,
            headers=headers,
            timeout=30,
        )

        # Если сервер вернул корректный JSON, то выводим его:
        try:
            data = response.json()
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Сохранил {file_name}")
            delay = random.uniform(10, 60)
            logger.info(f"Засыпаю на {delay} секунд")
            time.sleep(delay)

        except ValueError:
            print("Ошибка: ответ не содержит JSON")


def process_data():
    all_data = []
    json_files = list(json_directory.glob("*.json"))
    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        json_datas = data["data"]
        for json_data in json_datas:
            fName = json_data.get("fName", None)
            lName = json_data.get("lName", None)
            mName = json_data.get("mName", None)
            phone = json_data.get("phone", [])
            if phone:
                phone = phone[0]
            else:
                phone = None
            email = json_data.get("email", [])
            if email:
                email = email[0]
            else:
                email = None
            con_gorod = json_data.get("con_gorod", None)
            con_oblast = json_data.get("con_oblast", None)
            if con_oblast and isinstance(con_oblast, list):
                if (
                    len(con_oblast) == 1
                ):  # Проверяем, что список содержит ровно одно значение
                    con_oblast_value = con_oblast[0]
                    con_oblast_text = next(
                        (
                            option["text"]
                            for option in data["meta"]["fields"]["con_oblast"][
                                "options"
                            ]
                            if option["value"] == con_oblast_value
                        ),
                        None,
                    )
                    if con_oblast_text is None:
                        logger.info(
                            f"No matching option found for con_oblast value: {con_oblast_value}"
                        )
                else:
                    con_oblast_text = None
                    logger.info(
                        f"con_oblast is empty or has invalid length: {con_oblast}"
                    )
            else:
                con_oblast_text = None
                logger.info(
                    f"con_oblast is invalid: {con_oblast} (expected list, got {type(con_oblast)})"
                )
            leadsCount = json_data.get("leadsCount", None)  # Кол.Заявок
            leadsSalesCount = json_data.get("leadsSalesCount", None)  # Кол.Продаж
            leadsSalesAmount = json_data.get("leadsSalesAmount", None)  # СуммаПродаж
            comment = json_data.get("comment", None)  # Коментарий
            con_iDAMO = json_data.get("con_iDAMO", None)  # iDAMO
            con_markaModelGod = json_data.get("con_markaModelGod", None)  # МаркаМодель
            con_svaz = json_data.get("con_svaz", None)  # МаркаМодель

            result = {
                "Имя": fName,
                "Фамилия": lName,
                "Отчество": mName,
                "Телефон": phone,
                "email": email,
                "Комментарий": comment,
                "Кол.Заявок": leadsCount,
                "Кол.Продаж": leadsSalesCount,
                "СуммаПродаж": leadsSalesAmount,
                "Город": con_gorod,
                "Область": con_oblast_text,
                "ID AMO": con_iDAMO,
                "Скидака": con_svaz,
                "МаркаМодель": con_markaModelGod,
            }
            all_data.append(result)
    with open("file_name.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    df = pd.DataFrame(all_data)
    df.to_excel("financial_data.xlsx", index=False, engine="openpyxl")
    logger.info(f"Данные успешно записаны в 'financial_data.xlsx'")


if __name__ == "__main__":
    # get_json()
    process_data()
