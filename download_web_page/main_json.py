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


def get_json():
    for page in range(1, 2):
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
        cookies = {
            "XSRF-TOKEN": "eyJpdiI6Im5RRmNBL2JPeDJscnN3UlB3ZGtNTEE9PSIsInZhbHVlIjoiUGE4QWJsSVRPZWZSSUgxTHhTOS9xUTBpSHRwSnhCcVc3Yy9BL3g2STVKbkR0NFRaUVR2eldNRzZnTFU1end5WDg0OSt6RVRybE9ucXRqaEV6NFd4bHlKWmtxaHh2djc2NlBYRXRLKzltbEV4U3FtL2doZEQyWU5ZZHFYWU5NWm0iLCJtYWMiOiJiYTBkZjMyYmRmZmJhMzA0MjlmNDZjZjY1MTk3YjAwMDMyNjRlODBkNDA4YzVhM2RmNjViODZjODRkZjhiOGNkIiwidGFnIjoiIn0%3D",
            "tikleap_session": "eyJpdiI6IkRrbjNhN0pDc0NocVBGUUdpTU53Zmc9PSIsInZhbHVlIjoibXdDWWpPenVObjdJdGpIN3pGKzNQdlFPcnFjcEF4NTM0NDN3OTRMbTFGa0dVVm1OUVhBbHJkdTRYdDhZbnJMSHc4WnhGdE1nUlJHNTlMeG9oMG12UStIYlJqb2Y1QmhZb3NTS24yZ0orRHZwNXVKaUdLd3RZTVN1cGQ3Q0J5Y2kiLCJtYWMiOiJmMzk1YzE0MzgwYjY5MTRiMDllMTUyNWYyNTYzNWZhODQxOGYzOTRjZjc2OGIzZTkyNWQ3NjI4N2FjODUwNjBjIiwidGFnIjoiIn0%3D",
        }

        headers = {
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9,uk;q=0.8",
            "dnt": "1",
            "priority": "u=1, i",
            "referer": "https://www.tikleap.com/country/kz",
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        }
        response = requests.get(
            "https://www.tikleap.com/country-load-more/kz/2",
            cookies=cookies,
            headers=headers,
            timeout=30,
        )
        print(response.text)
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
    get_json()
    # process_data()
