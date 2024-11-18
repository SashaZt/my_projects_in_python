import json
import random
import re
import time
from pathlib import Path

import requests
from configuration.logger_setup import logger

current_directory = Path.cwd()

json_voltage_directory = current_directory / "json_voltage"
json_node_directory = current_directory / "json_node"
configuration_directory = current_directory / "configuration"

json_voltage_directory.mkdir(parents=True, exist_ok=True)
json_node_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

all_node_json_file = json_voltage_directory / "all_node.json"
config_txt_file = configuration_directory / "config.txt"
result_json_file = current_directory / "all_combined_data.json"


def random_pause(min_seconds=30, max_seconds=60):
    pause_duration = random.uniform(min_seconds, max_seconds)
    time.sleep(pause_duration)
    return pause_duration


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


def get_json_site():
    headers, cookies = get_cookies()
    site = "aescada.net/"
    params = {
        "input": {
            "args": {
                "competitors": [],
                "best_links_filter": "showAll",
                "backlinksFilter": None,
                "compareDate": ["Ago", "Month3"],
                "multiTarget": [
                    "Single",
                    {"protocol": "both", "mode": "subdomains", "target": site},
                ],
                "url": f"{site}",
                "protocol": "both",
                "mode": "subdomains",
            }
        }
    }

    urls = [
        "https://app.ahrefs.com/v4/seGetDomainRating",
        "https://app.ahrefs.com/v4/seBacklinksStats",
        "https://app.ahrefs.com/v4/seGetUrlRating",
        "https://app.ahrefs.com/v4/seGetMetrics",
        "https://app.ahrefs.com/v4/seGetMetricsByCountry",
    ]
    for url in urls:
        file_name = url.split("/")[-1]
        response = requests.get(
            url,
            params=params,
            cookies=cookies,
            headers=headers,
        )
        # Проверка кода ответа
        if response.status_code == 200:
            json_data = response.json()
            with open(f"{file_name}.json", "w", encoding="utf-8") as f:
                json.dump(
                    json_data, f, ensure_ascii=False, indent=4
                )  # Записываем в файл
        else:
            print(response.status_code)
        time.sleep(10)


def parsing_json():
    item = "seGetMetricsByCountry.json"
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
        country_00 = country_01 = country_02 = traffic_00 = traffic_01 = traffic_02 = (
            None
        )
    value = [
        country_00,
        traffic_00,
        country_01,
        traffic_01,
        country_02,
        traffic_02,
    ]
    logger.info(value)


if __name__ == "__main__":
    get_json_site()
    # parsing_json()
