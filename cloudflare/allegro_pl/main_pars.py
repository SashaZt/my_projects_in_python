import json
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from tqdm import tqdm

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
html_files_page_directory = current_directory / "html_files_page"
configuration_directory = current_directory / "configuration"
json_directory = current_directory / "json"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
html_files_page_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)

# Пути к файлам
output_csv_file = data_directory / "output.csv"
xlsx_result = data_directory / "result.xlsx"
json_result = data_directory / "result.json"
file_proxy = configuration_directory / "proxy.txt"
config_txt_file = configuration_directory / "config.txt"

max_workers = 5


def parse_ean_product(soup):
    """Извлекает EAN продукта."""
    ean_tag = soup.find('meta', itemprop='gtin')
    return ean_tag['content'] if ean_tag else None


def parse_brand_product(soup):
    """Извлекает бренд продукта."""
    brand_tag = soup.find('meta', itemprop='brand')
    return brand_tag['content'] if brand_tag else None


def parse_name_product(soup):
    """Извлекает название продукта."""
    name_tag = soup.find('meta', itemprop='name')
    return name_tag['content'] if name_tag else None


def parse_url_product(soup):
    """Извлекает URL продукта."""
    url_tag = soup.find('meta', itemprop='url')
    return url_tag['content'] if url_tag else None


def parse_price_product(soup):
    """Извлекает цену продукта."""
    price_tag = soup.find('meta', itemprop='price')
    return price_tag['content'] if price_tag else None


def parse_sales_product(soup):
    """Извлекает количество продаж продукта."""
    sales_tag = soup.find(string=lambda text: text and 'tę ofertę' in text)
    if sales_tag:
        sales_text = sales_tag.strip()
        sales_number = ''.join(filter(str.isdigit, sales_text))
        return int(sales_number) if sales_number else None
    return None


def parse_average_rating(soup):
    """Извлекает средний рейтинг продукта."""
    rating_tag = soup.find(
        'span', {'aria-label': lambda value: value and value.startswith('ocena:')})
    if rating_tag:
        rating_text = rating_tag.text.strip()
        return rating_text
    return None


def parse_weight_product(soup):
    """Извлекает вес продукта."""
    weight_tag = soup.find(
        'td', string=lambda text: text and 'Waga produktu' in text)
    if weight_tag:
        weight_value_tag = weight_tag.find_next_sibling('td')
        if weight_value_tag:
            weight_text = weight_value_tag.text.strip()
            return weight_text
    return None


def parse_condition(soup):
    """Извлекает состояние продукта."""
    condition_tag = soup.find('meta', itemprop='itemCondition')
    return condition_tag['content'].split('/')[-1] if condition_tag else None


def parse_warehouse_balances(soup):
    """Извлекает количество товара на складе."""
    script_tags = soup.find_all('script', type='application/json')
    for script_tag in script_tags:
        try:
            data = json.loads(script_tag.string)
            if isinstance(data, dict):
                # Проверка в структуре данных на наличие количества товара
                if 'watchButtonProps' in data and 'watchEventCustomParams' in data['watchButtonProps']:
                    item_data = data['watchButtonProps']['watchEventCustomParams'].get('item', {
                    })
                    if 'quantity' in item_data:
                        return item_data['quantity']
        except (json.JSONDecodeError, TypeError, KeyError):
            continue
    return None


def parse_single_html(file_html):
    """Парсит один HTML-файл для извлечения данных о продукте.

    Args:
        file_html (Path): Путь к HTML-файлу.

    Returns:
        dict or None: Словарь с данными о продукте или None, если данные не найдены.
    """
    with open(file_html, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")

    company_data = {
        "EAN_product": parse_ean_product(soup),
        "brand_product": parse_brand_product(soup),
        "name_product": parse_name_product(soup),
        "url_product": parse_url_product(soup),
        "price_product": parse_price_product(soup),
        "sales_product": parse_sales_product(soup),
        "weight_product": parse_weight_product(soup),
        "condition": parse_condition(soup),
        "warehouse_balances": parse_warehouse_balances(soup),
        "average_rating": parse_average_rating(soup)

    }

    return company_data


def parsing_html():
    """Выполняет многопоточный парсинг всех HTML-файлов в директории.

    Returns:
        list: Список словарей с данными о продуктах из всех файлов.
    """

    all_files = list_html()
    # Инициализация прогресс-бараedrpou.csv
    total_urls = len(all_files)
    progress_bar = tqdm(
        total=total_urls,
        desc="Обработка файлов",
        bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
    )

    # Многопоточная обработка файлов
    all_results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(parse_single_html, file_html): file_html
            for file_html in all_files
        }

        # Сбор результатов по мере завершения каждого потока
        for future in as_completed(futures):
            file_html = futures[future]
            try:
                result = future.result()
                if result is not None:
                    all_results.append(result)
            except Exception as e:
                logger.error(f"Ошибка при обработке файла {
                    file_html}: {e}")
                # Добавление трассировки стека
                logger.error(traceback.format_exc())
            finally:
                # Обновляем прогресс-бар после завершения обработки каждого файла
                progress_bar.update(1)

    # Закрываем прогресс-бар
    progress_bar.close()
    return all_results


def list_html():
    """Возвращает список HTML-файлов в заданной директории.

    Returns:
        list: Список файлов (Path) в директории html_files_directory.
    """

    # Получаем список всех файлов в html_files_directory
    file_list = [file for file in html_files_directory.iterdir()
                 if file.is_file()]

    logger.info(f"Всего файлов для обработки: {len(file_list)}")
    return file_list


def save_results_to_json(all_results):
    """Сохраняет результаты парсинга в JSON-файл.

    Args:
        all_results (list): Список словарей с данными о продуктах.
    """
    # Сохранить результаты в JSON файл
    try:
        with open(json_result, "w", encoding="utf-8") as json_file:
            json.dump(all_results, json_file, ensure_ascii=False, indent=4)
        logger.info(f"Данные успешно сохранены в файл {json_result}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в файл {
            json_result}: {e}")
        raise


def save_json_to_excel(json_file_path, excel_file_path):
    """Сохраняет данные из JSON-файла в Excel-файл с помощью pandas.

    Args:
        json_file_path (str or Path): Путь к JSON-файлу с данными.
        excel_file_path (str or Path): Путь к создаваемому Excel-файлу.
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        df = pd.DataFrame(data)
        df.to_excel(excel_file_path, index=False)
        logger.info(f"Данные успешно сохранены в Excel файл {excel_file_path}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в Excel файл {
                     excel_file_path}: {e}")
        raise


if __name__ == "__main__":
    all_results = parsing_html()
    save_results_to_json(all_results)
    save_json_to_excel(json_result, xlsx_result)
