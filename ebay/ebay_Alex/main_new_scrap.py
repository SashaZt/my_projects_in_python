import csv
import json
import logging
import os
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import lxml
import pandas as pd
from bs4 import BeautifulSoup
from logger import logger
from tqdm import tqdm

# Глобальные переменные для хранения всех уникальных ключей характеристик
SPEC_KEYS = set()
BATCH_SIZE = 1000  # Размер пакета для периодической записи результатов


def get_breadcrumbList(soup):
    """Извлечение хлебных крошек из HTML"""
    try:
        breadcrumb_list = []
        breadcrumb_nav = soup.find("nav", {"class": "breadcrumbs"})
        if breadcrumb_nav:
            for item in breadcrumb_nav.find_all("a"):
                text = item.get_text(strip=True)
                if text:
                    breadcrumb_list.append(text)
        return " > ".join(breadcrumb_list)
    except Exception:
        return ""


def extract_specifications(soup):
    """Извлечение характеристик товара"""
    specifications = {}

    # Метод 1: Извлечение из x-prp-product-details (первый формат)
    specs_div = soup.find("div", {"class": "x-prp-product-details"})
    if specs_div:
        # Используем CSS-селектор для прямого поиска необходимых элементов
        for row in specs_div.select("div.x-prp-product-details_row"):
            for col in row.select("div.x-prp-product-details_col"):
                name_elem = col.select_one("span.x-prp-product-details_name")
                value_elem = col.select_one("span.x-prp-product-details_value")
                if name_elem and value_elem:
                    spec_name = name_elem.get_text(strip=True)
                    spec_value = value_elem.get_text(strip=True)
                    specifications[spec_name] = spec_value

    # Метод 2: Извлечение из vim x-about-this-item (второй формат)
    if not specifications:
        # Используем CSS-селектор для прямого поиска необходимых элементов
        about_items = soup.select("div.vim.x-about-this-item dl.ux-labels-values")
        for item in about_items:
            name_elem = item.select_one("dt.ux-labels-values__labels")
            if not name_elem:
                continue

            spec_name = name_elem.get_text(strip=True)
            value_elem = item.select_one(
                "dd.ux-labels-values__values div.ux-labels-values__values-content > div"
            )
            if not value_elem:
                continue

            # Извлекаем текст и очищаем его
            if value_elem.select_one("span.ux-expandable-textual-display-block-inline"):
                text_span = value_elem.select_one("span[data-testid='text']")
                spec_value = (
                    text_span.get_text(strip=True)
                    if text_span
                    else value_elem.get_text(strip=True).split("Read more")[0]
                )
            else:
                spec_value = value_elem.get_text(strip=True)

            # Очищаем значение
            spec_value = re.sub(
                r"Read more|Read Less|opens in a new window or tab|about the seller notes",
                "",
                spec_value,
            )
            spec_value = spec_value.strip('"')

            specifications[spec_name] = spec_value

    return specifications


def process_html_file(html_file):
    """Обработка одного HTML-файла"""
    try:
        with open(html_file, encoding="utf-8") as file:
            content = file.read()

        # Используем lxml для быстрого парсинга
        soup = BeautifulSoup(content, "lxml")

        # Инициализируем словарь для данных
        product_data = {"filename": os.path.basename(html_file)}

        # Извлекаем хлебные крошки
        product_data["category"] = get_breadcrumbList(soup)

        # Извлекаем URL из <meta property="og:url">
        url_meta = soup.find("meta", {"property": "og:url"})
        product_data["url"] = url_meta.get("content", "") if url_meta else ""

        # Извлекаем заголовок
        title_tag = soup.find("div", {"data-testid": "x-item-title"})
        product_data["title"] = (
            title_tag.find("span").get_text(strip=True)
            if title_tag and title_tag.find("span")
            else ""
        )

        # Извлекаем цену - используем CSS-селектор
        price_span = soup.select_one("div.x-price-primary span.ux-textspans")
        if price_span:
            price_text = price_span.get_text(strip=True)
            price = "".join(filter(lambda x: x.isdigit() or x == ".", price_text))
            product_data["price"] = price
        else:
            product_data["price"] = ""

        # Извлекаем изображения - используем CSS-селектор и limit=3
        images = []
        for img in soup.select(
            "div.ux-image-carousel-item.image-treatment.image img", limit=3
        ):
            src = img.get("data-zoom-src")
            if src:
                images.append(src)

        product_data["image_1"] = images[0] if len(images) > 0 else ""
        product_data["image_2"] = images[1] if len(images) > 1 else ""
        product_data["image_3"] = images[2] if len(images) > 2 else ""

        # Извлекаем состояние товара - используем CSS-селектор
        condition_span = soup.select_one(
            "div.vim.x-item-condition span[data-testid='ux-textual-display']"
        )
        product_data["condition"] = (
            condition_span.get_text(strip=True) if condition_span else ""
        )

        # Извлекаем информацию о возврате - используем CSS-селектор
        returns_div = soup.select_one(
            "div[data-testid='x-returns-minview'] div.ux-labels-values__values-content, div.vim.x-returns-minview div.ux-labels-values__values-content"
        )
        if returns_div:
            returns_parts = [
                span.get_text(strip=True)
                for span in returns_div.find_all(["span", "button"])
                if span.get_text(strip=True)
            ]
            product_data["returns"] = " ".join(returns_parts)
        else:
            product_data["returns"] = ""

        # Извлекаем информацию о доставке и shipping
        shipping_container = soup.select_one(
            "div[data-testid='d-shipping-minview'], div.vim.d-shipping-minview"
        )
        if shipping_container:
            # Shipping
            shipping_block = shipping_container.select_one(
                "div[data-testid='ux-labels-values'][class*='ux-labels-values--shipping']"
            )
            if shipping_block:
                shipping_content = shipping_block.select_one(
                    "div.ux-labels-values__values-content"
                )
                if shipping_content:
                    first_line_parts = [
                        span.get_text(strip=True)
                        for span in shipping_content.select(
                            "div:first-child > span.ux-textspans"
                        )
                        if span.get_text(strip=True)
                        and not span.get_text(strip=True).startswith("See details")
                    ]

                    location_span = shipping_content.select_one(
                        "div:nth-child(2) > span.ux-textspans--SECONDARY"
                    )
                    location_text = (
                        location_span.get_text(strip=True) if location_span else ""
                    )

                    shipping_info = []
                    if first_line_parts:
                        shipping_info.append(" ".join(first_line_parts))
                    if location_text:
                        shipping_info.append(location_text)

                    combined_shipping = shipping_container.find(
                        "span", string=lambda s: s and "Save on combined shipping" in s
                    )
                    if combined_shipping:
                        shipping_info.append("Save on combined shipping")

                    product_data["shipping"] = ", ".join(shipping_info)
                else:
                    product_data["shipping"] = ""
            else:
                product_data["shipping"] = ""

            # Delivery
            delivery_block = shipping_container.select_one(
                "div.ux-labels-values--deliverto"
            )
            if delivery_block:
                delivery_content_div = delivery_block.select_one(
                    "div.ux-labels-values__values-content"
                )
                if delivery_content_div:
                    delivery_info = []

                    # Даты доставки
                    first_div = delivery_content_div.select_one("div")
                    if first_div:
                        delivery_text = ""
                        main_spans = first_div.select("span.ux-textspans")
                        for span in main_spans:
                            if "ux-textspans__custom-view" not in span.get(
                                "class", []
                            ) and not span.has_attr("role"):
                                delivery_text += span.get_text(strip=True) + " "

                        if delivery_text.strip():
                            delivery_info.append(delivery_text.strip())

                    # Примечание о сроках
                    divs = delivery_content_div.select("div")
                    if len(divs) > 1:
                        notes = [
                            span.get_text(strip=True)
                            for span in divs[1].select(
                                "span[class*='ux-textspans--SECONDARY']"
                            )
                        ]
                        if notes:
                            delivery_info.append(" ".join(notes))

                    # Информация об отправке
                    if len(divs) > 2:
                        shipping_info = []
                        shipping_info.extend(
                            [
                                span.get_text(strip=True)
                                for span in divs[2].select(
                                    "span[class*='ux-textspans--SECONDARY']"
                                )
                            ]
                        )
                        shipping_info.extend(
                            [
                                span.get_text(strip=True)
                                for span in divs[2].select(
                                    "a span[class*='ux-textspans--SECONDARY']"
                                )
                            ]
                        )

                        if shipping_info:
                            delivery_info.append(" ".join(shipping_info))

                    product_data["delivery"] = ", ".join(delivery_info)
                else:
                    product_data["delivery"] = ""
            else:
                product_data["delivery"] = ""
        else:
            product_data["shipping"] = ""
            product_data["delivery"] = ""

        # Извлекаем характеристики
        specifications = extract_specifications(soup)

        # Сохраняем характеристики как JSON-строку
        product_data["specifications"] = json.dumps(specifications, ensure_ascii=False)

        # Добавляем характеристики как отдельные поля в product_data
        for key, value in specifications.items():
            product_data[key] = value

            # Добавляем ключ в множество всех ключей (глобальная переменная)
            global SPEC_KEYS
            SPEC_KEYS.add(key)

        # Заменяем переносы строк на пробелы
        for key, value in product_data.items():
            if isinstance(value, str):
                product_data[key] = value.replace("\n", " ").replace("\r", "")

        return product_data

    except Exception as e:
        logger.error(f"Ошибка при обработке {os.path.basename(html_file)}: {str(e)}")
        return {
            "filename": os.path.basename(html_file),
            "title": "",
            "url": "",
            "price": "",
            "image_1": "",
            "image_2": "",
            "image_3": "",
            "condition": "",
            "returns": "",
            "shipping": "",
            "delivery": "",
        }


def save_batch_to_csv(data_batch, output_file, all_columns=None, mode="a"):
    """Сохранение пакета данных в CSV"""
    if not data_batch:
        return

    # Определяем все колонки, если не переданы
    if not all_columns:
        # Базовые колонки
        base_columns = [
            "filename",
            "title",
            "category",
            "url",
            "price",
            "image_1",
            "image_2",
            "image_3",
            "condition",
            "returns",
            "shipping",
            "delivery",
        ]
        all_columns = base_columns + sorted(SPEC_KEYS)

    # Создаем DataFrame и записываем в CSV
    df_data = []
    for item in data_batch:
        row = {col: item.get(col, "") for col in all_columns}
        df_data.append(row)

    df = pd.DataFrame(df_data, columns=all_columns)

    # Записываем в CSV с правильными настройками
    df.to_csv(
        output_file,
        index=False,
        encoding="utf-8",
        sep=";",
        quoting=csv.QUOTE_ALL,
        escapechar="\\",
        doublequote=True,
        quotechar='"',
        mode=mode,  # Режим записи: 'w' - перезапись, 'a' - добавление
        header=(mode == "w"),  # Заголовки только при первой записи
    )


def main(html_directory, output_file="product_details.csv", max_workers=None):
    """Основная функция для обработки HTML-файлов с использованием многопроцессорности"""
    html_directory = Path(html_directory)
    files = list(html_directory.glob("*.html"))
    total_files = len(files)

    logger.info(f"Начало обработки {total_files} HTML-файлов...")
    print(f"Начало обработки {total_files} HTML-файлов...")

    # Переменные для хранения промежуточных результатов
    data_batch = []
    processed_count = 0

    # Создаем пустой файл с заголовками
    open(output_file, "w").close()

    # Используем ProcessPoolExecutor для параллельной обработки
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Создаем задачи для обработки файлов
        futures = {
            executor.submit(process_html_file, str(file)): file for file in files
        }

        # Используем tqdm для прогресс-бара
        for future in tqdm(
            as_completed(futures), total=total_files, desc="Обработка файлов"
        ):
            file = futures[future]
            try:
                # Получаем результат обработки файла
                result = future.result()
                if result:
                    data_batch.append(result)
                    processed_count += 1

                # Периодически сохраняем результаты
                if len(data_batch) >= BATCH_SIZE:
                    # Определяем все колонки на основе текущих данных
                    base_columns = [
                        "filename",
                        "title",
                        "category",
                        "url",
                        "price",
                        "image_1",
                        "image_2",
                        "image_3",
                        "condition",
                        "returns",
                        "shipping",
                        "delivery",
                    ]
                    all_columns = base_columns + sorted(SPEC_KEYS)

                    # Записываем текущий пакет в CSV
                    save_mode = "w" if processed_count <= BATCH_SIZE else "a"
                    save_batch_to_csv(
                        data_batch, output_file, all_columns, mode=save_mode
                    )

                    # Очищаем пакет
                    data_batch = []

                    # Выводим прогресс
                    logger.info(f"Обработано {processed_count} файлов из {total_files}")
                    print(
                        f"Обработано {processed_count} файлов из {total_files}",
                        end="\r",
                    )

            except Exception as e:
                logger.error(f"Ошибка при обработке {file}: {str(e)}")

    # Сохраняем оставшиеся данные
    if data_batch:
        base_columns = [
            "filename",
            "title",
            "category",
            "url",
            "price",
            "image_1",
            "image_2",
            "image_3",
            "condition",
            "returns",
            "shipping",
            "delivery",
        ]
        all_columns = base_columns + sorted(SPEC_KEYS)

        save_mode = "w" if processed_count <= BATCH_SIZE else "a"
        save_batch_to_csv(data_batch, output_file, all_columns, mode=save_mode)

    logger.info(f"Обработка завершена. Всего обработано файлов: {processed_count}")
    print(f"\nОбработка завершена. Всего обработано файлов: {processed_count}")
    print(f"Данные сохранены в {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Парсинг HTML-файлов eBay.")
    parser.add_argument("html_dir", help="Директория с HTML-файлами")
    parser.add_argument(
        "--output", default="product_details.csv", help="Имя выходного CSV-файла"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Количество рабочих процессов (по умолчанию = количество ядер CPU)",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=1000,
        help="Размер пакета для периодического сохранения (по умолчанию = 1000)",
    )

    args = parser.parse_args()

    # Устанавливаем размер пакета
    BATCH_SIZE = args.batch

    # Запускаем основную функцию
    main(args.html_dir, args.output, args.workers)
