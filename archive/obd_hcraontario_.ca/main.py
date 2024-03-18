# -*- coding: utf-8 -*-
import os
import glob
import json
import csv
from collections import defaultdict
import requests
import json
import re
import csv
import requests
import os
import glob
import random
from proxi import proxies
from bs4 import BeautifulSoup
import time

current_directory = os.getcwd()
temp_directory = "temp"
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
summary_path = os.path.join(temp_directory, "summary")
contact_path = os.path.join(temp_directory, "contact")

#скачиваю основную страницу с данными
def proba():

    cookies = {
        "ARRAffinity": "9dbd9775f7b40d4bcba2cb924d9b50a65fe5685a62f1bd21d92e4be6e85df8c6",
        "ARRAffinitySameSite": "9dbd9775f7b40d4bcba2cb924d9b50a65fe5685a62f1bd21d92e4be6e85df8c6",
    }

    headers = {
        "authority": "obd.hcraontario.ca",
        "accept": "application/json, text/plain, */*",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "no-cache",
        # 'cookie': 'ARRAffinity=9dbd9775f7b40d4bcba2cb924d9b50a65fe5685a62f1bd21d92e4be6e85df8c6; ARRAffinitySameSite=9dbd9775f7b40d4bcba2cb924d9b50a65fe5685a62f1bd21d92e4be6e85df8c6',
        "dnt": "1",
        "pragma": "no-cache",
        "referer": "https://obd.hcraontario.ca/buildersearchresults?&page=1",
        "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://obd.hcraontario.ca/api/builders?&page=1",
        cookies=cookies,
        headers=headers,
    )
    json_data = response.json()
    with open(f"test.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл

# Создаю временные папки
def delete_old_data():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, contact_path, summary_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

# Случайное прокси
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

# собираем ACCOUNTNUMBER со страницы
def parsing():
    with open(f"test.json", "r") as f:
        data_json = json.load(f)
    all_accountnumber = []
    for d in data_json:
        accountnumber = d["ACCOUNTNUMBER"]
        all_accountnumber.append(accountnumber)

    return all_accountnumber

# Получаем id компании
def get_all_id():

    all_data = parsing()
    for a in all_data:
        return a

# получение и сохранение данных
def fetch_and_save_data(api_url, save_path):

    all_data = parsing()
    for a in all_data:
        cookies = {
            "ARRAffinity": "9dbd9775f7b40d4bcba2cb924d9b50a65fe5685a62f1bd21d92e4be6e85df8c6",
            "ARRAffinitySameSite": "9dbd9775f7b40d4bcba2cb924d9b50a65fe5685a62f1bd21d92e4be6e85df8c6",
        }

        headers = {
            "authority": "obd.hcraontario.ca",
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
            "cache-control": "no-cache",
            # 'cookie': 'ARRAffinity=9dbd9775f7b40d4bcba2cb924d9b50a65fe5685a62f1bd21d92e4be6e85df8c6; ARRAffinitySameSite=9dbd9775f7b40d4bcba2cb924d9b50a65fe5685a62f1bd21d92e4be6e85df8c6',
            "dnt": "1",
            "pragma": "no-cache",
            "referer": "https://obd.hcraontario.ca/profile/B48156",
            "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }

        params = {
            "id": a,
        }

        filename = os.path.join(save_path, f"{params['id']}.json")
        if not os.path.exists(filename):
            proxies = proxy_random()
            response = requests.get(
                api_url,
                params=params,
                cookies=cookies,
                headers=headers,
                proxies=proxies,
            )
            attempts = 0
            success = False

            while attempts < 3 and not success:
                response = requests.get(
                    api_url,
                    params=params,
                    cookies=cookies,
                    headers=headers,
                    proxies=proxies,
                )
                if response.status_code == 200:
                    json_data = response.json()
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=4)
                    success = True
                else:
                    attempts += 1
                    time.sleep(1)  # Пауза в 1 секунду

            if not success:
                print(
                    f"Не удалось получить данные после {attempts} попыток для ID: {a}"
                )


def parse_contact_info(contact_info):
    if not contact_info:
        return None, None, None, None

    # Удаление указанных фраз
    phrases_to_remove = [
        "Public Contact Number",
        "Public Fax Number",
        "Public Alternate Phone Number",
    ]
    for phrase in phrases_to_remove:
        contact_info = contact_info.replace(phrase, "")

    # Ищем электронную почту
    email_match = re.search(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", contact_info
    )
    email = email_match.group(0) if email_match else None

    # Извлекаем и удаляем электронную почту из строки
    if email:
        contact_info = contact_info.replace(email, "")
    # Ищем веб-сайт
    website_match = re.search(
        r"(?:http[s]?://)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", contact_info
    )
    website = website_match.group(0) if website_match else None

    # Извлекаем и удаляем веб-сайт из строки
    if website:
        contact_info = contact_info.replace(website, "")

    # Ищем телефоны
    # Ищем телефоны в формате (123) 456-7890 или 123-456-7890
    phones = re.findall(
        r"\(\d{3}\)\s?\d{3}[- ]?\d{4}|\d{3}-\d{3}-\d{4}|\d{3} \d{3}-\d{4}", contact_info
    )

    # Удаляем телефоны из строки, чтобы оставить только адрес
    for phone in phones:
        contact_info = contact_info.replace(phone, "")

    address = contact_info.strip()

    # Возвращаем адрес, строку с телефонами, веб-сайт и электронную почту
    return address, ", ".join(phones), website, email

def check_files_existence(a, contact_path, summary_path):
    """
    Проверяет, существуют ли оба файла для данного идентификатора a
    в папках contact_path и summary_path.
    """
    filename_contact = os.path.join(contact_path, f"{a}.json")
    filename_summary = os.path.join(summary_path, f"{a}.json")
    return os.path.exists(filename_contact) and os.path.exists(filename_summary)

def pars():

    # Получаем список всех файлов .json в папке summary
    summary_files = glob.glob(os.path.join(summary_path, '*.json'))

    # Заготовка для инициализации CSV
    fields = None
    with open("output.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = None
        
        # Проходим по всем файлам в папке summary
        for summary_file in summary_files:
            # Извлекаем название файла для проверки наличия в папке contact
            filename = os.path.basename(summary_file)
            contact_file = os.path.join(contact_path, filename)
            
            # Проверяем, существует ли аналогичный файл в папке contact
            if os.path.exists(contact_file):
                try:
                    # Загружаем данные из обоих файлов
                    with open(summary_file, "r") as f:
                        summary_data = json.load(f)
                    with open(contact_file, "r") as f:
                        contact_data = json.load(f)
                    json_contact = contact_data
                    json_summary = summary_data
                    aggregated_data = {}

                    for item in json_contact:
                        name = item["TO"]
                        role = item["Relationship Type"]
                        contact_info = item["PDO_CONTACT_INFO"]

                        # Если имя уже есть в агрегированных данных
                        if name in aggregated_data:
                            # Добавляем новую роль, если она уникальна
                            aggregated_data[name]["roles"].add(role)
                        else:
                            # Создаем новую запись для этого имени
                            aggregated_data[name] = {
                                "roles": {role},
                                "contact_info": contact_info,
                            }
                    full_info = []
                    # Форматирование и вывод агрегированных данных
                    for name, info in aggregated_data.items():
                        roles_str = ", ".join(info["roles"])
                        contact_info = {
                            "name_contact": name,
                            "roles_str": roles_str,
                            "info_contact": info["contact_info"],
                        }
                        full_info.append(contact_info)

                    # Инициализация словаря для хранения списков значений по каждому ключу
                    aggregated_info = defaultdict(list)

                    # Форматирование и агрегирование данных
                    for item in full_info:
                        for key, value in item.items():
                            # Добавляем значение в список для соответствующего ключа
                            aggregated_info[key].append(value)

                    # Преобразование агрегированных списков в строки, с фильтрацией None значений
                    for key in aggregated_info:
                        # Фильтруем список, удаляя None и преобразуем оставшиеся элементы в строки
                        filtered_values = [
                            str(v) for v in aggregated_info[key] if v is not None
                        ]
                        aggregated_info[key] = ", ".join(filtered_values)

                    # Вывод результатов
                    for js in json_summary:
                        summary_info = {
                            "account number": js.get("Account Number", None),
                            "umbrella": js.get("Umbrella", None),
                            "umbrella id": js.get("Umbrella ID", None),
                            "vb_name": js.get("VB_NAME", None),
                            "operatingname": js.get("OPERATINGNAME", None),
                            "city": js.get("CITY", None),
                            "hcra_initiallicensedate": js.get(
                                "HCRA_INITIALLICENSEDATE", None
                            ),
                            "licence_status": js.get("LICENCE_STATUS", None),
                            "hcra_licensereneedon": js.get("HCRA_LICENSERENEWEDON", None),
                            "expiry date": js.get("Expiry Date", None),
                            "renl_in_process_flag": js.get("RENL_IN_PROCESS_FLAG", None),
                            "address": js.get("ADDRESS", None),
                            "telephone": js.get("TELEPHONE", None),
                            "fax": js.get("FAX", None),
                            "websiteurl": js.get("WEBSITEURL", None),
                            "email": js.get("EMAIL", None),
                            "accountnumber": js.get("ACCOUNTNUMBER", None),
                            "total outstanding amount": js.get(
                                "Total Outstanding Amount", None
                            ),
                            "tab": js.get("TAB", None),
                            "breach": js.get("BREACH", None),
                            "summ_freehold": js.get("SUMM_FREEHOLD", None),
                            "summ_condo": js.get("SUMM_CONDO", None),
                            "summ_total": js.get("SUMM_TOTAL", None),
                            "summ_cc": js.get("SUMM_CC", None),
                            "summ_minor": js.get("SUMM_MINOR", None),
                            "summ_minor_amt": js.get("SUMM_MINOR_AMT", None),
                            "summ_major": js.get("SUMM_MAJOR", None),
                            "summ_major_amt": js.get("SUMM_MAJOR_AMT", None),
                            "summ_total_claims": js.get("SUMM_TOTAL_CLAIMS", None),
                        }  # type: ignore
                    combined_info = {**summary_info, **aggregated_info}

                    for key, value in combined_info.items():
                        if isinstance(
                            value, list
                        ):  # Проверяем, является ли значение списком
                            # Фильтруем список, удаляя элементы None, и преобразуем оставшиеся элементы в строки
                            filtered_values = [str(v) for v in value if v is not None]
                            combined_info[key] = ", ".join(filtered_values)

                    # Если fields еще не определены, определяем их на основе первой итерации и инициализируем writer
                    if fields is None:
                        fields = list(combined_info.keys())
                        writer = csv.DictWriter(csvfile, fieldnames=fields, delimiter=";")
                        writer.writeheader()

                    # Записываем данные текущей итерации
                    writer.writerow(combined_info)
                except Exception as e:
                    print(f"Произошла ошибка при обработке файла {e}")
                    continue  # Пропускаем итерацию в случае ошибки
            # # Запись в CSV
            # with open("output.csv", "w", newline="", encoding="utf-8") as csvfile:
            #     writer = csv.DictWriter(csvfile, fieldnames=fields, delimiter=";")
            #     writer.writeheader()
            #     writer.writerow(combined_info)  # Используем combined_info для записи


if __name__ == "__main__":
    # delete_old_data()
    proba()
    # parsing()
    # url_summary = "https://obd.hcraontario.ca/api/buildersummary"
    # url_contact = "https://obd.hcraontario.ca/api/builderPDOs"
    # fetch_and_save_data(url_summary, summary_path)
    # fetch_and_save_data(url_contact, contact_path)
    pars()
