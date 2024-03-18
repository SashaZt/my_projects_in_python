# -*- coding: utf-8 -*-
import json
import os
import requests
import glob
import time
from config import cookies, headers
from proxi import proxies
import random
from datetime import datetime

current_directory = os.getcwd()
temp_directory = "temp"
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
all_hotels = os.path.join(temp_path, "all_hotels")
hotel_path = os.path.join(temp_path, "hotel")


def proxy_random():
    """
    Функция для случайного прокси
    """
    proxy = random.choice(proxies)
    proxy_host = proxy[0]
    proxy_port = proxy[1]
    proxy_user = proxy[2]
    proxy_pass = proxy[3]
    formatted_proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"

    # Возвращаем словарь с прокси
    return {"http": formatted_proxy, "https": formatted_proxy}


def get_param_hotels():
    folder = os.path.join(all_hotels, "*.json")
    files_json = glob.glob(folder)
    allparams = []  # Инициализируем список за пределами цикла обработки файлов
    # unique_iata_codes = set()
    for item in files_json:
        with open(item, "r", encoding="utf-8") as f:
            data_json = json.load(f)
        for j in data_json:
            # # Собираем уникальные Iata коды
            # przystanki = j.get("Przystanki", [])
            # for przystanek in przystanki:
            #     # Извлекаем Iata код и добавляем его в множество
            #     iata_code = przystanek.get("Iata")
            #     if iata_code:
            #         unique_iata_codes.add(iata_code)
            basic_information = j.get("BazoweInformacje", {})
            if basic_information.get("TypWycieczki") == "wypoczynek":
                hotelurl = basic_information["OfertaURLDlaGoogle"].split("/")[-1]

                regiony = (
                    basic_information.get("Regiony", [""])[0]
                    .lower()
                    .rstrip()
                    .replace(" ", "-")
                )
                typwycieczki = basic_information.get("TypWycieczki", "")
                liczbadni = basic_information.get("LiczbaDni", "")
            else:
                continue
            przystanki = j.get("Przystanki", [])
            iata_codes = [
                przystanek["Iata"] for przystanek in przystanki if "Iata" in przystanek
            ]

            wyzywienia = j.get("Wyzywienia", [])

            if wyzywienia:
                wyzywienia = wyzywienia[0].get("URL", None)
            else:
                # Устанавливаем wyzywienia в None, если список пуст
                wyzywienia = None
            produkturl = f"{regiony}-{typwycieczki}"
            terminwyjazdu = j["TerminWyjazdu"]
            date_obj = datetime.strptime(terminwyjazdu, "%Y-%m-%dT%H:%M:%SZ")
            # Форматирование объекта datetime обратно в строку, содержащую только дату
            terminwyjazdu = date_obj.strftime("%Y-%m-%d")
            summary_info = {
                "produkturl": produkturl,
                "hotelurl": hotelurl,
                "wyzywienia": wyzywienia,
                "iata_codes": iata_codes,
                "terminwyjazdu": terminwyjazdu,
                "liczbadni": liczbadni,
            }

            allparams.append(summary_info)
    with open("allparams.json", "w", encoding="utf-8") as f:
        json.dump(allparams, f, ensure_ascii=False, indent=4)  # Записываем в файл
    # unique_iata_codes_list = list(unique_iata_codes)

    # print(unique_iata_codes_list)
    return allparams  # Возвращаем allparams после обработки всех файлов


def get_json():
    allparams = get_param_hotels()
    for params in allparams:
        produkturl = params["produkturl"]
        hotelurl = params["hotelurl"]
        wyzywienia = params["wyzywienia"]
        iata_codes = params["iata_codes"]
        terminwyjazdu = params["terminwyjazdu"]
        liczbadni = params["liczbadni"]

        for i in iata_codes:
            iata_directory = os.path.join(hotel_path, i)
            os.makedirs(iata_directory, exist_ok=True)
            proxi = proxy_random()
            json_data = {
                "HotelUrl": hotelurl,
                "ProduktUrl": produkturl,
                "LiczbaPokoi": 1,
                "Dlugosc": liczbadni,
                "TerminWyjazdu": terminwyjazdu,
                "Iata": i,
                "DatyUrodzenia": [
                    "1994-01-01",
                    "1994-01-01",
                ],
                "Wyzywienie": wyzywienia,
                "CzyV2": True,
            }
            filename = os.path.join(iata_directory, f"{hotelurl}.json")
            if not os.path.exists(filename):
                response = requests.post(
                    "https://r.pl/api/wyszukiwarka/wyszukaj-kalkulator",
                    cookies=cookies,
                    headers=headers,
                    json=json_data,
                    proxies=proxi,
                )

                hotelurl = json_data["HotelUrl"]

                json_data_r = response.json()

                # wybrana_dict = json_data_r.get("Wybrana")
                # wybrana = wybrana_dict.get("Cena") if wybrana_dict else None

                # if wybrana is not None and wybrana != 0:
                # if wybrana_dict is not None:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(
                        json_data_r, f, ensure_ascii=False, indent=4
                    )  # Записываем в файл
                time.sleep(5)
        # return hotelurl


def pars_json():
    # folder = os.path.join(hotel_path, "*.json")
    # files_json = glob.glob(folder)

    all_data = {}

    # Перебираем каждую поддиректорию в директории hotel
    for root, dirs, files in os.walk(hotel_path):
        for dir_name in dirs:
            # Строим путь к поддиректории
            sub_folder_path = os.path.join(hotel_path, dir_name)
            # Получаем список всех JSON файлов в текущей поддиректории
            files_json = glob.glob(os.path.join(sub_folder_path, "*.json"))

            for item in files_json:
                filename = os.path.basename(item)

                hotel_name = os.path.splitext(filename)[0]

                with open(item, "r", encoding="utf-8") as f:
                    data_json = json.load(f)

                terminy = data_json.get("Terminy", [])
                file_data = {}

                for t in terminy:
                    term = t["Dlugosc"]
                    terminy_data = t.get("Terminy", [])

                    term_data_list = [
                        {
                            "date_from": tt["Termin"],
                            "date_until": tt["DataKoniec"],
                            "price": tt["Cena"],
                            "price_per_person": tt["CenaZaOsobe"],
                        }
                        for tt in terminy_data
                    ]

                    if term not in file_data:
                        file_data[term] = term_data_list
                    else:
                        file_data[term].extend(term_data_list)

                # Если отель уже есть в all_data, добавляем или обновляем данные по текущей поддиректории
                if hotel_name not in all_data:
                    all_data[hotel_name] = {dir_name: file_data}
                else:
                    if dir_name not in all_data[hotel_name]:
                        all_data[hotel_name][dir_name] = file_data
                    else:
                        for term, data_list in file_data.items():
                            if term not in all_data[hotel_name][dir_name]:
                                all_data[hotel_name][dir_name][term] = data_list
                            else:
                                all_data[hotel_name][dir_name][term].extend(data_list)

    # Выводим итоговый словарь с данными
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)  # Записываем в файл


if __name__ == "__main__":
    get_param_hotels()
    get_json()
    pars_json()
