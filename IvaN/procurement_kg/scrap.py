import asyncio
import json
import os
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

from config import Config, logger, paths


class HTMLExtractor:
    def __init__(self, directory_path):
        self.directory_path = Path(directory_path)
        self.data = []

    def extract_company_info(self, html_content):
        """Извлекает информацию о компании из HTML"""
        soup = BeautifulSoup(html_content, "html.parser")

        # Инициализируем словарь с пустыми значениями
        company_info = {
            "name": "",
            "description": "",
            "categories": "",
            "address": "",
            "email": "",
            "phone": "",
            "image_url": "",
        }

        content_div = soup.find("div", class_="content")
        if not content_div:
            return company_info

        # Название компании
        title = content_div.find("h2", class_="entry_title")
        if title:
            company_info["name"] = title.get_text(strip=True)

        # Описание (первый <p> после заголовка)
        description_p = content_div.find("p")
        if description_p:
            company_info["description"] = description_p.get_text(strip=True)

        # Категории
        badge = content_div.find("span", class_="badge")
        if badge:
            company_info["categories"] = badge.get_text(strip=True)

        # Изображение
        img = content_div.find("img", class_="img-responsive")
        if img and img.get("src"):
            company_info["image_url"] = img.get("src")

        # Контактная информация
        contact_div = content_div.find("div", class_="contact-info")
        if contact_div:
            # Адрес
            address_row = contact_div.find(
                "p", string=lambda text: text and "Адрес:" in text
            )
            if not address_row:
                for p in contact_div.find_all("p"):
                    strong = p.find("strong")
                    if strong and "Адрес:" in strong.get_text():
                        address_row = p
                        break

            if address_row:
                span = address_row.find("span")
                if span:
                    company_info["address"] = span.get_text(strip=True)

            # Email
            email_row = contact_div.find(
                "p", string=lambda text: text and "Email:" in text
            )
            if not email_row:
                for p in contact_div.find_all("p"):
                    strong = p.find("strong")
                    if strong and "Email:" in strong.get_text():
                        email_row = p
                        break

            if email_row:
                span = email_row.find("span")
                if span:
                    company_info["email"] = span.get_text(strip=True)

            # Телефон
            phone_row = contact_div.find(
                "p", string=lambda text: text and "Тел:" in text
            )
            if not phone_row:
                for p in contact_div.find_all("p"):
                    strong = p.find("strong")
                    if strong and "Тел:" in strong.get_text():
                        phone_row = p
                        break

            if phone_row:
                span = phone_row.find("span")
                if span:
                    company_info["phone"] = span.get_text(strip=True)

        return company_info

    async def process_html_file(self, file_path):
        """Обрабатывает один HTML файл"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            company_info = self.extract_company_info(html_content)
            company_info["file_name"] = file_path.name

            logger.info(f"Обработан файл: {file_path.name}")
            return company_info

        except Exception as e:
            logger.error(f"Ошибка обработки файла {file_path}: {e}")
            return None

    async def process_directory(self):
        """Обрабатывает все HTML файлы в директории"""
        html_files = list(self.directory_path.glob("*.html"))

        if not html_files:
            logger.warning("HTML файлы не найдены в директории")
            return

        logger.info(f"Найдено {len(html_files)} HTML файлов")

        tasks = []
        for file_path in html_files:
            task = asyncio.create_task(self.process_html_file(file_path))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Собираем успешные результаты
        for result in results:
            if isinstance(result, dict):
                self.data.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Ошибка: {result}")

    def save_to_json(self, filename="companies.json"):
        """Сохраняет данные в JSON файл"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"Данные сохранены в {filename}")
        except Exception as e:
            logger.error(f"Ошибка сохранения JSON: {e}")

    def save_to_excel(self, filename="companies.xlsx"):
        """Сохраняет данные в Excel файл"""
        try:
            df = pd.DataFrame(self.data)
            df.to_excel(filename, index=False, engine="openpyxl")
            logger.info(f"Данные сохранены в {filename}")
        except Exception as e:
            logger.error(f"Ошибка сохранения Excel: {e}")

    async def run(self):
        """Основная функция"""
        logger.info(f"Начинаем обработку директории: {self.directory_path}")

        await self.process_directory()

        if self.data:
            logger.info(f"Обработано {len(self.data)} компаний")
            self.save_to_json()
            self.save_to_excel()

            # Выводим статистику
            logger.info("Статистика:")
            logger.info(f"- Всего компаний: {len(self.data)}")
            logger.info(
                f"- С адресом: {sum(1 for item in self.data if item['address'])}"
            )
            logger.info(f"- С email: {sum(1 for item in self.data if item['email'])}")
            logger.info(
                f"- С телефоном: {sum(1 for item in self.data if item['phone'])}"
            )
        else:
            logger.warning("Данные не найдены")


async def main():

    extractor = HTMLExtractor(paths.html)
    await extractor.run()


if __name__ == "__main__":
    asyncio.run(main())
