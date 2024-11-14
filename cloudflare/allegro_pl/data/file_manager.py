# data/file_manager.py
import json
import logging

import pandas as pd
from configuration.config import Config


class FileManager:
    @staticmethod
    def read_cities_from_csv(file_path):
        df = pd.read_csv(file_path)
        return df["url"].tolist()

    @staticmethod
    def save_to_csv(data, file_path):
        pd.DataFrame(data, columns=["url"]).to_csv(
            file_path, index=False, encoding="utf-8"
        )
        logging.info(f"Data saved to {file_path}")

    @staticmethod
    def save_results_to_json(data, file_path):
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {file_path}")

    @staticmethod
    def save_json_to_excel(json_file_path, excel_file_path):
        with open(json_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        pd.DataFrame(data).to_excel(excel_file_path, index=False)
        logging.info(f"Data saved to Excel file {excel_file_path}")
