from pathlib import Path

import requests
from configuration.logger_setup import logger


class Downloader:
    def __init__(self, api_key, html_page_directory, html_files_directory):
        self.api_key = api_key
        self.html_page_directory = html_page_directory
        self.html_files_directory = html_files_directory

    def get_all_page_html(self, url_start):
        html_company = self.html_page_directory / "url_start.html"
        payload = {"api_key": self.api_key, "url": url_start}

        if html_company.exists():
            logger.warning(f"Файл {html_company} уже существует, пропускаем загрузку.")
        else:
            r = requests.get("https://api.scraperapi.com/", params=payload, timeout=60)
            if r.status_code == 200:
                with open(html_company, "w", encoding="utf-8") as file:
                    file.write(r.text)
                logger.info(f"Сохранена первая страница: {html_company}")
            else:
                logger.error(f"Ошибка при запросе первой страницы: {r.status_code}")

    def get_url(self, url_list):
        for url in url_list:
            html_company = self.html_files_directory / f"{url.split('/')[-1]}.html"
            if html_company.exists():
                logger.warning(f"Файл {html_company} уже существует, пропускаем.")
                continue
            payload = {"api_key": self.api_key, "url": url}
            r = requests.get("https://api.scraperapi.com/", params=payload, timeout=30)
            if r.status_code == 200:
                with open(html_company, "w", encoding="utf-8") as file:
                    file.write(r.text)
                logger.info(f"Сохранен файл: {html_company}")
            else:
                logger.warning(f"Ошибка {r.status_code} при загрузке URL: {url}")
