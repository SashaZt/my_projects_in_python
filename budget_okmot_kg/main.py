import asyncio
import json
from pathlib import Path

import pandas as pd
import requests
from configuration.logger_setup import logger

# Указываем пути к файлам и папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
json_files_directory = current_directory / "json"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
json_files_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

csv_output_file = data_directory / "output.csv"
json_result = data_directory / "result.json"
xlsx_result = data_directory / "result.xlsx"


def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


def get_json():

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "DNT": "1",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    tins = read_cities_from_csv(csv_output_file)
    for tin in tins[:1]:
        tin = "00000000000000"
        years = ["2021", "2022", "2023", "2024"]
        for year in years:
            out_json_file = json_files_directory / f"{tin}_{year}.json"
            params = {
                "tin": tin,
                "year": year,
                "startMonth": "1",
                "endMonth": "12",
            }
            logger.info(params)
            r = requests.get(
                "https://budget.okmot.kg/api/income/tin",
                params=params,
                headers=headers,
                timeout=10,
            )
            if r.status_code == 200:
                json_data = r.json()
                # Записываем в файл
                with open(out_json_file, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
            else:
                logger.error(r.status_code)


if __name__ == "__main__":
    get_json()
