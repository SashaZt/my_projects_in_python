import asyncio
import json
import os
import random
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import aiofiles
import pandas as pd
import requests
from configuration.logger_setup import logger
from playwright.async_api import async_playwright
from tqdm import tqdm

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
html_page_directory = current_directory / "html_page"
xml_files_directory = current_directory / "xml_files"
json_responses_directory = current_directory / "json_responses"

data_directory.mkdir(parents=True, exist_ok=True)
html_page_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
xml_files_directory.mkdir(exist_ok=True, parents=True)


output_csv_file = data_directory / "output.csv"
file_json = json_responses_directory / "post_response.json"


def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


async def main(urls_site):
    async with async_playwright() as p:
        for url in urls_site:
            # Запуск браузера без загрузки изображений
            browser = await p.chromium.launch(
                headless=False
            )  # Установите headless=True для скрытого режима
            context = await browser.new_context()

            # Отключение загрузки изображений
            await context.route(
                "**/*",
                lambda route, request: (
                    asyncio.create_task(route.continue_())
                    if request.resource_type != "image"
                    else asyncio.create_task(route.abort())
                ),
            )

            # Создаем новую страницу для каждого URL
            page = await context.new_page()
            category_name = url.rsplit("/", maxsplit=1)[-1]

            # Переход на начальную страницу
            await page.goto(url)
            await asyncio.sleep(5)  # Пауза на 5 секунд

            # Проверяем наличие пагинации
            # Замена селектора пагинации на указанный XPath
            pagination_selector = '//div[@class="paging-container pull-right"]//ul[@class="pagination pagination-sm"]//i[@class="fa fa-step-forward"]'

            try:
                # Ждем появления пагинации
                locator = await page.wait_for_selector(
                    pagination_selector, timeout=5000
                )
                pagination_exists = await locator.is_visible()

                if pagination_exists:
                    logger.info(f"Пагинация найдена для категории {category_name}.")
                else:
                    raise Exception("Пагинация отсутствует")

                # Нажатие на кнопку "вперед" пока она доступна
                next_button_selector = "div.list-main.products-list > div.products-list-content > div:nth-child(5) > ul > li:nth-child(8) > a"
                while True:
                    try:
                        # Получаем номер страницы
                        number = await page.locator(
                            "div:nth-child(5) > ul > li.active > a"
                        ).inner_text()

                        # Сохраняем текущую страницу
                        output_html_file = (
                            html_page_directory / f"{category_name}_0{number}.html"
                        )
                        content = await page.content()
                        await save_html_content(content, output_html_file)

                        # Проверяем наличие кнопки "вперед"
                        next_button = page.locator(next_button_selector).nth(0)
                        if await next_button.is_visible():
                            await next_button.click()
                            await asyncio.sleep(5)  # Пауза на 5 секунд
                            await page.wait_for_load_state("networkidle")
                        else:
                            logger.info(
                                f"Больше страниц нет для категории {category_name}."
                            )
                            break
                    except Exception as e:
                        logger.error(
                            f"Ошибка при обработке страницы категории {category_name}: {e}"
                        )
                        break
            except Exception as e:
                logger.warning(
                    f"Пагинация отсутствует для категории {category_name} или произошла ошибка: {e}"
                )

                try:
                    # Сохраняем текущую страницу как единственную
                    number = "1"
                    output_html_file = (
                        html_page_directory / f"{category_name}_0{number}.html"
                    )
                    content = await page.content()
                    await save_html_content(content, output_html_file)
                    logger.info(
                        f"Сохранена единственная страница для категории {category_name}."
                    )
                except Exception as save_error:
                    logger.error(
                        f"Ошибка при сохранении страницы для категории {category_name}: {save_error}"
                    )
            finally:
                # Закрываем страницу после обработки
                await browser.close()


async def save_html_content(content, output_html_file):
    # Сохраняем HTML-контент
    with output_html_file.open("w", encoding="utf-8") as file:
        file.write(content)
    logger.info(f"Сохранено: {output_html_file}")


if __name__ == "__main__":
    urls = read_cities_from_csv(output_csv_file)
    asyncio.run(main(urls))
