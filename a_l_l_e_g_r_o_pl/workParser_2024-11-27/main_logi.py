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
    consecutive_no_additions = 0  # Счетчик файлов, где не добавлено уникальных ссылок
    max_no_additions = 2  # Лимит на количество подряд файлов без добавлений

    for html_file in html_page_directory.glob("*.html"):

        with open(html_file, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")

        # Поиск всех элементов <span> с текстом, содержащим "osób"
        result = soup.find_all("span", string=lambda t: t and "osób" in t)
        url_r = set()
        for rs in result:
            osob = int(rs.text.replace(" osób", ""))
            # Проверяем условие
            if osob >= 50:
                # Поднимаемся к <article> и ищем ссылку <a>
                article = rs.find_parent("article")
                if article:
                    link_raw = article.find("a", href=True)
                    if link_raw:
                        link = link_raw["href"]
                        url_r.add(link)

        # Логируем результаты текущего файла
        # logger.info(f"Файл: {html_file.name}, Найдено ссылок: {len(url_r)}")

        # Состояние all_data до обновления
        before_update = len(all_data)

        # Обновляем общий набор уникальных ссылок
        all_data.update(url_r)

        # Количество уникальных ссылок, добавленных из текущего файла
        added_count = len(all_data) - before_update
        logger.info(
            f"Файл: {html_file.name}, Уникальных ссылок добавлено: {added_count}"
        )

        # Проверяем, были ли добавлены уникальные ссылки
        if added_count == 0:
            consecutive_no_additions += 1
            logger.info(
                f"Файл: {html_file.name}, Ничего нового не добавлено. Подряд файлов без добавлений: {consecutive_no_additions}"
            )
            # Проверяем, достигли ли лимита
            if consecutive_no_additions >= max_no_additions:
                logger.info(
                    "Достигнут лимит файлов без добавлений. Завершаем обработку."
                )
                break
        else:
            consecutive_no_additions = (
                0  # Сбрасываем счетчик, если добавлены уникальные ссылки
            )

    # Логируем общее количество уникальных ссылок
    logger.info(f"Общее количество уникальных ссылок: {len(all_data)}")
    return all_data


if __name__ == "__main__":
    parsing_page()
