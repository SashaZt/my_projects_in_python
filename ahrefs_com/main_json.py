import json
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from configuration.logger_setup import logger

current_directory = Path.cwd()

json_data_directory = current_directory / "json_data"
configuration_directory = current_directory / "configuration"
data_directory = current_directory / "data"

json_data_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

csv_output_file = data_directory / "output.csv"
config_txt_file = configuration_directory / "config.txt"


# Случайная пауза
def random_pause(min_seconds=30, max_seconds=60):
    pause_duration = random.uniform(min_seconds, max_seconds)
    logger.info(f"Пауза {pause_duration}")
    time.sleep(pause_duration)
    return pause_duration


# Список сайтов
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


# Получение куки
def get_cookies():
    # Чтение строки curl из файла
    with open(config_txt_file, "r", encoding="utf-8") as f:
        curl_text = f.read()

    # Инициализация словарей для заголовков и кук
    headers = {}
    cookies = {}

    # Извлечение всех заголовков из параметров `-H`
    header_matches = re.findall(r"-H '([^:]+):\s?([^']+)'", curl_text)
    for header, value in header_matches:
        if header.lower() == "cookie":
            # Обработка куки отдельно, разделяя их по `;`
            cookies = {
                k.strip(): v
                for pair in value.split("; ")
                if "=" in pair
                for k, v in [pair.split("=", 1)]
            }
        else:
            headers[header] = value

    return headers, cookies


# Скачиваем данные по каждому сайту
def get_json_site_data():
    sites = read_cities_from_csv(csv_output_file)
    headers, cookies = get_cookies()
    for site in sites[:101]:
        logger.info(f"Получаем данные по сайту {site}")
        site_directory = json_data_directory / site
        site_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Создал директорию {site_directory}")
        params = {
            "input": '{"args":{"competitors":[],"best_links_filter":"showAll","backlinksFilter":null,"compareDate":["Ago","Month3"],"multiTarget":["Single",{"protocol":"both","mode":"subdomains","target":"example.com/"}],"url":"example.com/","protocol":"both","mode":"subdomains"}}',
        }

        # Заменяем все вхождения 'aescada.net' на значение переменной `site`
        params["input"] = params["input"].replace("example.com", site)

        urls = [
            "https://app.ahrefs.com/v4/seGetDomainRating",
            "https://app.ahrefs.com/v4/seBacklinksStats",
            "https://app.ahrefs.com/v4/seGetUrlRating",
            "https://app.ahrefs.com/v4/seGetMetrics",
            "https://app.ahrefs.com/v4/seGetMetricsByCountry",
        ]
        for url in urls:
            file_name = url.rsplit("/", maxsplit=1)[-1]

            json_path = site_directory / f"{file_name}.json"
            if json_path.exists():
                continue
            response = requests.get(
                url,
                params=params,
                cookies=cookies,
                headers=headers,
                timeout=60,
            )
            # Проверка кода ответа
            if response.status_code == 200:
                json_data = response.json()
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                logger.info(f"Файл сохранен {json_path}")
            else:
                logger.error(f"Ошибка {response.status_code} для {file_name}")
            pause = random_pause(10, 20)  # Пауза в диапазоне 5-10 секунд
        get_json_graf(site, site_directory, cookies, headers)
        pause = random_pause(10, 20)  # Пауза в диапазоне 5-10 секунд


def get_json_graf(site, site_directory, cookies, headers):
    url = "https://app.ahrefs.com/v4/seGetMetricsHistory"
    file_name = url.rsplit("/", maxsplit=1)[-1]

    json_path = site_directory / f"{file_name}.json"
    if json_path.exists():
        return None
    params = {
        "input": '{"chart":{"grouping":"monthly","from":"all"},"params":{"timeout":null,"shape":null,"drop_for_report__order_by":null,"drop_for_report__offset":0,"drop_for_report__size":0,"filter":null},"args":{"competitors":[],"best_links_filter":"showAll","backlinksFilter":null,"compareDate":["Ago","Month3"],"multiTarget":["Single",{"protocol":"both","mode":"subdomains","target":"example.com/"}],"url":"example.com/","protocol":"both","mode":"subdomains"}}',
    }
    # Заменяем все вхождения 'aescada.net' на значение переменной `site`
    params["input"] = params["input"].replace("example.com", site)
    response = requests.get(
        url,
        params=params,
        headers=headers,
        cookies=cookies,
        timeout=60,
    )
    # Проверка кода ответа
    if response.status_code == 200:
        json_data = response.json()
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
        logger.info(f"Файл сохранен {json_path}")
    else:
        logger.error(response.status_code)
    time.sleep(10)


def parsing_json_BacklinksStats(item):
    with open(item, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    try:
        backlinks_value = (
            json_data[1].get("backlinks", {}).get("current", {}).get("value")
        )
        refdomains_value = (
            json_data[1].get("refdomains", {}).get("current", {}).get("value")
        )
        all_data = {
            "backlinks_value": backlinks_value,
            "refdomains_value": refdomains_value,
        }
        return all_data
    except (IndexError, TypeError) as e:
        print(f"Error extracting data: {e}")
        return None


def parsing_json_GetDomainRating(item):
    with open(item, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    try:
        domainRating_value = json_data[1].get("domainRating", {}).get("value")
        all_data = {
            "domainRating_value": domainRating_value,
        }
        return all_data
    except (IndexError, TypeError) as e:
        print(f"Error extracting data: {e}")
        return None


def parsing_json_GetMetrics(item):
    with open(item, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    try:
        organic_traffic_value = (
            json_data[1].get("organic", {}).get("traffic", {}).get("value")
        )
        organic_keywords_value = (
            json_data[1].get("organic", {}).get("keywords", {}).get("value")
        )
        all_data = {
            "organic_traffic_value": organic_traffic_value,
            "organic_keywords_value": organic_keywords_value,
        }
        return all_data
    except (IndexError, TypeError) as e:
        print(f"Error extracting data: {e}")
        return None


def parsing_json_GetUrlRating(item):
    with open(item, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    try:
        urlRating_value = json_data[1].get("urlRating", {}).get("value")
        all_data = {
            "urlRating_value": urlRating_value,
        }
        return all_data
    except (IndexError, TypeError) as e:
        print(f"Error extracting data: {e}")
        return None


def parsing_json_GetMetricsByCountry(item):
    with open(item, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    metrics = json_data[1].get("metrics", [])
    if len(metrics) > 2:
        country_00 = metrics[0].get("country")
        traffic_00 = metrics[0].get("organic", {}).get("traffic", {}).get("value")
        country_01 = metrics[1].get("country")
        traffic_01 = metrics[1].get("organic", {}).get("traffic", {}).get("value")
        country_02 = metrics[2].get("country")
        traffic_02 = metrics[2].get("organic", {}).get("traffic", {}).get("value")
    else:
        # Значения по умолчанию, если данных по странам недостаточно
        country_00 = country_01 = country_02 = None
        traffic_00 = traffic_01 = traffic_02 = 0

    # Считаем общий трафик
    total_traffic = traffic_00 + traffic_01 + traffic_02

    # Рассчитываем долю трафика для каждой страны (в процентах)
    def calculate_percentage(traffic, total):
        return round((traffic / total * 100), 2) if total > 0 else 0

    traffic_share_00 = int(calculate_percentage(traffic_00, total_traffic))
    traffic_share_01 = int(calculate_percentage(traffic_01, total_traffic))
    traffic_share_02 = int(calculate_percentage(traffic_02, total_traffic))
    if traffic_share_00 > 0:
        traffic_share_00 = f"{traffic_share_00}%"
    if traffic_share_01 > 0:
        traffic_share_01 = f"{traffic_share_01}%"
    if traffic_share_02 > 0:
        traffic_share_02 = f"{traffic_share_02}%"
    # Формируем итоговый словарь с результатами
    all_data = {
        "country_00": country_00,
        "traffic_00": traffic_00,
        "traffic_share_00": traffic_share_00,
        "country_01": country_01,
        "traffic_01": traffic_01,
        "traffic_share_01": traffic_share_01,
        "country_02": country_02,
        "traffic_02": traffic_02,
        "traffic_share_02": traffic_share_02,
    }

    return all_data


def parsing_json_GetMetricsHistory(item):
    # Открываем и читаем JSON файл
    with open(item, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    logger.info(item)
    # Проверяем, что json_data - это список и индекс 1 существует
    if not isinstance(json_data, list) or len(json_data) < 2:
        print("Unexpected JSON structure.")
        return []

    # Получаем данные из второго элемента списка
    metrics_data = json_data[1]

    # Получаем текущую дату и генерируем список дат - текущий месяц и предыдущие 5 месяцев
    current_date = datetime.now().replace(day=1)

    # dates = [
    #     (current_date.replace(day=1) - timedelta(days=30 * i))
    #     .replace(day=1)
    #     .strftime("%Y-%m-%d")
    #     for i in range(5, -1, -1)
    # ]

    # Получаем трафик из metrics_data
    traffic_data = []
    try:
        # Извлекаем список rows из metrics_data
        metrics = metrics_data.get("rows", [])

        if metrics:
            # Берём последние 6 элементов из списка metrics
            last_entries = metrics[-6:]

            # Итерируемся по последним 6 элементам и извлекаем нужные значения
            for entry in last_entries:
                date = entry.get("date", "Unknown Date")
                organic_traffic = entry.get("organic", {}).get("traffic", 0)
                # Формируем результат для каждого элемента
                traffic_data.append(
                    {
                        "date": date,
                        "traffic": organic_traffic,
                    }
                )

    except KeyError as e:
        print(f"Error processing JSON data: {e}")

    # Логируем полученные данные
    return traffic_data


def get_domain_name(subfolder):
    # Извлекаем имя домена из пути подкаталога, например "aescada.net"
    return subfolder.name


def write_data():
    flattened_data = []

    # Группируем файлы JSON по подкаталогам
    subfolder_files = {}
    for json_file in json_data_directory.rglob("*.json"):
        subfolder = json_file.parent
        if subfolder not in subfolder_files:
            subfolder_files[subfolder] = []
        subfolder_files[subfolder].append(json_file)

    # Обрабатываем каждый подкаталог отдельно
    for subfolder, files in subfolder_files.items():
        backlinksstats = {}
        getdomainrating = {}
        getmetrics = {}
        geturlrating = {}
        getmetricsbycountry = {}
        getmetricshistory = []
        domain = get_domain_name(subfolder)  # Используем имя подкаталога как домен

        # Читаем каждый файл в подкаталоге и выполняем соответствующий парсинг
        for json_file in files:
            if json_file.name == "seBacklinksStats.json":
                backlinksstats = parsing_json_BacklinksStats(json_file)
            elif json_file.name == "seGetDomainRating.json":
                getdomainrating = parsing_json_GetDomainRating(json_file)
            elif json_file.name == "seGetMetrics.json":
                getmetrics = parsing_json_GetMetrics(json_file)
            elif json_file.name == "seGetUrlRating.json":
                geturlrating = parsing_json_GetUrlRating(json_file)
            elif json_file.name == "seGetMetricsByCountry.json":
                getmetricsbycountry = parsing_json_GetMetricsByCountry(json_file)
            elif json_file.name == "seGetMetricsHistory.json":
                getmetricshistory = parsing_json_GetMetricsHistory(
                    json_file
                )  # Ожидается, что это список словарей

        # Собираем все результаты в один словарь
        all_result = {
            domain: [
                backlinksstats,
                getdomainrating,
                getmetrics,
                geturlrating,
                getmetricsbycountry,
            ]
        }

        # Преобразуем getmetricshistory в плоский словарь
        metricshistory_combined = {}
        if getmetricshistory:
            for idx, metric in enumerate(getmetricshistory):
                prefix = f"history_{idx+1}_"
                for key, value in metric.items():
                    metricshistory_combined[f"{prefix}{key}"] = value

        # Добавляем данные в domain_data
        for domain, metrics_list in all_result.items():
            domain_data = {"domain": domain}
            for metric_dict in metrics_list:
                if metric_dict is not None:
                    domain_data.update(metric_dict)

            # Добавляем объединённые данные getmetricshistory в domain_data
            domain_data.update(metricshistory_combined)

            # Добавляем итоговую строку в список flattened_data
            flattened_data.append(domain_data)

    # Создаем DataFrame из подготовленных данных
    data_df = pd.DataFrame(flattened_data)

    # Сохраняем данные в новый Excel файл
    output_path = "All_Result.xlsx"
    data_df.to_excel(output_path, index=False)


if __name__ == "__main__":
    # get_json_site_data()
    write_data()
