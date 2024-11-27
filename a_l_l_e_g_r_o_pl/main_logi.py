import asyncio
import os
import shutil
from parser import Parser
from pathlib import Path

from bs4 import BeautifulSoup
from configuration.logger_setup import logger

# Указываем пути к файлам и папкам
current_directory = Path.cwd()
html_page_directory = current_directory / "html_page_copy"


def parsing_page():
    all_data = set()

    for html_file in html_page_directory.glob("*.html"):

        with open(html_file, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")
        # Поиск нужного элемента <span> с текстом "614 osób"
        result = soup.find_all("span", string=lambda t: t and "osób" in t)
        url_r = set()
        for rs in result:
            osob = int(rs.text.replace(" osób", ""))
            # Если число больше или равно 50
            if osob >= 50:
                # Поднимаемся к родителю <article>
                article = rs.find_parent("article")
                if article:
                    # Ищем ссылку <a> внутри <article>
                    link_raw = article.find("a", href=True)
                    if link_raw:
                        link = link_raw["href"]
                        url_r.add(link)

        # Логируем результаты текущего файла
        logger.info(f"File: {html_file.name}, Found links in file: {len(url_r)}")

        # Состояние all_data до обновления
        before_update = len(all_data)

        # Обновляем общий набор уникальных ссылок
        all_data.update(url_r)

        # Количество уникальных ссылок, добавленных из текущего файла
        added_count = len(all_data) - before_update
        logger.info(
            f"File: {html_file.name}, Unique links added to all_data: {added_count}"
        )

        # Если были добавлены уникальные ссылки, переходим к следующему файлу
        if added_count != 0:
            continue

    # Логируем общее количество уникальных ссылок
    logger.info(f"Total unique links in all_data: {len(all_data)}")


if __name__ == "__main__":
    parsing_page()
