import random
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import pandas as pd
from openpyxl.utils import get_column_letter
import os
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

current_directory = Path.cwd()
images_directory = current_directory / "images"
html_directory = current_directory / "html"
images_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)
output_file = current_directory / "output.xlsx"

def main_realoem(code, max_retries=10):

    params = {
        "q": code,
    }
    proxies = {
        "http": "http://scraperapi:6c54502fd688c7ce737f1c650444884a@proxy-server.scraperapi.com:8001",
        "https": "http://scraperapi:6c54502fd688c7ce737f1c650444884a@proxy-server.scraperapi.com:8001",
    }
    try:
        retries = 0
        while retries < max_retries:
            response = requests.get(
                "https://www.realoem.com/bmw/enUS/partxref",
                params=params,
                proxies=proxies,
                timeout=100,
                verify=False,
            )
            if response.status_code == 200:
                # Сохранение HTML-страницы целиком
                with open("realoem.html", "w", encoding="utf-8") as file:
                    file.write(response.text)
                # Использование:
                if find_error(response.text):  # Если ошибка найдена, пропускаем
                    logger.error(f'Такого кода {code} нету')
                    break
                list_urls = scap_realoem(response.text)
                list_urls = process_urls(list_urls)
                process_parts_urls(list_urls)
                break
            else:
                logger.warning(
                    f"Attempt {
                        retries + 1} failed for URL: {code}. Status code: {response.status_code}"
                )
                retries += 1
                if retries < max_retries:
                    logger.info(
                        f"Waiting 5 seconds before retry {
                            retries + 1}/{max_retries}"
                    )
                    time.sleep(5)  # Ждем 5 секунд перед следующей попыткой
                else:
                    logger.error(
                        f"All {max_retries} attempts failed for URL: {code}"
                    )
            # Добавляем задержку между запросами
            time.sleep(random.uniform(1, 3))
    except (requests.exceptions.RequestException, requests.exceptions.ReadTimeout) as retry_e:
        logger.error(f"Request error on attempt {retries + 1}: {str(retry_e)}")
        retries += 1
        if retries < max_retries:
            wait_time = 5 * retries  # Увеличиваем время ожидания с каждой попыткой
            logger.info(f"Waiting {wait_time} seconds before retry {
                        retries + 1}/{max_retries}")
            time.sleep(wait_time)
        else:
            logger.error(f"All {max_retries} attempts failed")
def find_error(content):
    soup = BeautifulSoup(content, "lxml")
    return bool(soup.find("div", {"class": "error vs2"}))  # Возвращает True, если найден элемент

def scap_realoem(content):
    extracted_data = []
    # Парсим HTML с помощью BeautifulSoup
    soup = BeautifulSoup(content, "lxml")

    url_tag = soup.find("div", {"class": "partSearchResults"})
    if url_tag:
        for a in url_tag.find_all("a"):
            url = f"https://www.realoem.com{a.get('href')}"
            extracted_data.append(url)
    return extracted_data


def process_urls(urls, max_retries=10):
    proxies = {
        "http": "http://scraperapi:6c54502fd688c7ce737f1c650444884a@proxy-server.scraperapi.com:8001",
        "https": "http://scraperapi:6c54502fd688c7ce737f1c650444884a@proxy-server.scraperapi.com:8001",
    }
    results = []
    for url in urls:
        try:
            retries = 0
            while retries < max_retries:
                # Парсим URL на компоненты
                parsed_url = urlparse(url)

                # Получаем параметры из URL
                params = dict(parse_qs(parsed_url.query))
                # Преобразуем значения из списков в строки
                params = {k: v[0] for k, v in params.items()}

                logger.info(f"Processing URL with params: {params}")

                response = requests.get(
                    "https://www.realoem.com/bmw/enUS/partxref",
                    params=params,
                    proxies=proxies,
                    timeout=100,
                    verify=False,
                )

                if response.status_code == 200:
                    list_urls = scap_realoem(response.text)
                    results.append(list_urls)
                    logger.info(f"Successfully processed URL: {url}")
                    break
                else:
                    logger.warning(
                        f"Attempt {
                            retries + 1} failed for URL: {url}. Status code: {response.status_code}"
                    )
                    retries += 1
                    if retries < max_retries:
                        logger.info(
                            f"Waiting 5 seconds before retry {
                                retries + 1}/{max_retries}"
                        )
                        time.sleep(5)  # Ждем 5 секунд перед следующей попыткой
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed for URL: {url}"
                        )
                # Добавляем задержку между запросами
                time.sleep(random.uniform(1, 3))
        except (requests.exceptions.RequestException, requests.exceptions.ReadTimeout) as retry_e:
            logger.error(f"Request error on attempt {retries + 1}: {str(retry_e)}")
            retries += 1
            if retries < max_retries:
                wait_time = 5 * retries  # Увеличиваем время ожидания с каждой попыткой
                logger.info(f"Waiting {wait_time} seconds before retry {
                            retries + 1}/{max_retries}")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed")

    return results


def create_filename_from_url(url):
    parsed_url = urlparse(url)
    params = dict(parse_qs(parsed_url.query))

    # Получаем id и diagId
    car_id = params.get("id", [""])[0]
    diag_id = params.get("diagId", [""])[0]

    # Получаем номер детали из фрагмента
    part_number = parsed_url.fragment

    # Формируем имя файла
    file_name = f"{car_id}_{diag_id}_{part_number}"

    return file_name


def process_parts_urls(nested_urls, max_retries=10):
    results = []
    proxies = {
        "http": "http://scraperapi:6c54502fd688c7ce737f1c650444884a@proxy-server.scraperapi.com:8001",
        "https": "http://scraperapi:6c54502fd688c7ce737f1c650444884a@proxy-server.scraperapi.com:8001",
    }
    urls = [url for sublist in nested_urls for url in sublist]
    for url in urls:
        retries = 0
        while retries < max_retries:
            try:
                parsed_url = urlparse(url)
                file_name = create_filename_from_url(url)
                html_file = html_directory / f"{file_name}.html"
                if html_file.exists():
                    break  # Пропускаем, если файл уже существует
                params = dict(parse_qs(parsed_url.query))
                params = {k: v[0] for k, v in params.items()}

                part_number = parsed_url.fragment if parsed_url.fragment else None
                if part_number:
                    params["highlight"] = part_number

                logger.info(f"Processing URL with params: {params}")

                response = requests.get(
                    "https://www.realoem.com/bmw/enUS/showparts",
                    params=params,
                    proxies=proxies,
                    timeout=100,
                    verify=False,
                )

                if response.status_code == 200:
                    with open(html_file, "w", encoding="utf-8") as file:
                        file.write(response.text)
                    # results.append(response.text)
                    logger.info(f"Successfully processed URL: {url}")
                    break
                else:
                    logger.warning(
                        f"Attempt {
                            retries + 1} failed for URL: {url}. Status code: {response.status_code}"
                    )
                    retries += 1
                    if retries < max_retries:
                        logger.info(
                            f"Waiting 5 seconds before retry {
                                retries + 1}/{max_retries}"
                        )
                        time.sleep(5)  # Ждем 5 секунд перед следующей попыткой
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed for URL: {url}"
                        )

            except (requests.exceptions.RequestException, requests.exceptions.ReadTimeout) as retry_e:
                logger.error(f"Request error on attempt {
                             retries + 1}: {str(retry_e)}")
                retries += 1
                if retries < max_retries:
                    wait_time = 5 * retries  # Увеличиваем время ожидания с каждой попыткой
                    logger.info(f"Waiting {wait_time} seconds before retry {
                                retries + 1}/{max_retries}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed")

        # Задержка между разными URL (только если был успешный запрос)
        if retries < max_retries:
            time.sleep(random.uniform(1, 3))

    return results


def combine_parts_and_images(parts_data, images_data):
    for part_number, part_info in parts_data.items():
        position = f"pos{part_info['position'].zfill(2)}"
        if position in images_data:
            part_info['image_info'] = images_data[position]

    return parts_data


def parse_data_from_html(soup, image_url, html_file):
    parts_table = soup.find('table', {'id': 'partsList'})
    if not parts_table:
        logger.error("Table with id 'partsList' not found")
        return {}

    all_parts_data = []
    rows = parts_table.find_all('tr')[1:]  # Пропускаем заголовок

    current_condition = ""

    for row in rows:
        cells = row.find_all('td')
        if not cells or len(cells) < 2:  # Проверяем минимальное количество ячеек
            continue

        # Проверяем, является ли это строкой с условиями
        first_cell_text = cells[0].text.strip()
        second_cell_text = cells[1].text.strip()

        # Если это строка с условиями
        if (not first_cell_text and
                second_cell_text.startswith("For vehicles with")):
            try:
                parameters = cells[2].text.strip() if len(cells) > 2 else ""
                current_condition = f"{
                    second_cell_text} | Parameters: {parameters}"
            except Exception as e:
                logger.error(f"Error processing condition row in {html_file}: {str(e)}")
            continue

        try:
            # Проверяем, что у нас достаточно ячеек для детали
            if len(cells) < 7:
                continue

            part_number = cells[6].text.strip()
            if part_number:
                part_data = {
                    "part_number": part_number,
                    'position': cells[0].text.strip(),
                    'description': cells[1].text.strip(),
                    'supplier': cells[2].text.strip(),
                    'quantity': cells[3].text.strip() if len(cells) > 3 else "",
                    'from_date': cells[4].text.strip() if len(cells) > 4 else "",
                    'up_to_date': cells[5].text.strip() if len(cells) > 5 else "",
                    'price': cells[7].text.strip() if len(cells) > 7 else "",
                    'notes': cells[9].text.strip() if len(cells) > 9 else "",
                    'is_highlighted': 'poshl' in row.get('class', []),
                    'condition': current_condition,
                    'image_url': image_url,
                }
                all_parts_data.append(part_data)

        except Exception as e:
            logger.error(f"Error processing row in {html_file}: {str(e)}")
            logger.error(f"Row content: {cells}")
            continue

    return all_parts_data


# Использование в основном коде:
def parse_images_data(soup):
    img_div = soup.find('div', {'id': 'partsimg'})
    if img_div:
        img_tag = img_div.find('img')
        if img_tag:
            url = img_tag.get('src')
            full_url = f"https://www.realoem.com{url}"
            local_image_path = download_and_save_image(full_url)
            return local_image_path
    return None


def scrap():
    all_data = []
    # Добавляем проверку существования директории
    if not html_directory.exists():
        logger.error(f"Directory {html_directory} does not exist")
        return

    html_files = list(html_directory.glob("*.html"))
    logger.info(f"Found {len(html_files)} HTML files")

    for html_file in html_files:
        # model = get_models(html_file)
        # logger.info(f"Processing file: {html_file}")
        try:
            with html_file.open(encoding="utf-8") as file:
                content = file.read()
                soup = BeautifulSoup(content, "lxml")

                # Проверяем, что контент не пустой
                if not content.strip():
                    logger.error(f"Empty file: {html_file}")
                    continue

                images_data = parse_images_data(soup)
                parts_data = parse_data_from_html(soup, images_data, html_file)
                all_data.extend(parts_data)  # Используем extend вместо append

        except Exception as e:
            logger.error(f"Error processing file {html_file}: {e}")

    if all_data:
        save_to_excel(all_data)
    return all_data

# def get_models(html_files):
    # Преобразуем PosixPath в строку
    path_str = str(html_files)
    parts = path_str.split('_')
    if len(parts) > 1:  # Проверяем, что в строке есть хотя бы один символ подчеркивания
        last_part = parts[-1]

        # Убираем .html из конца строки, если оно там есть
        if last_part.endswith('.html'):
            number = last_part[:-5]

            # Проверяем, что оставшаяся часть - это действительно число
            if number.isdigit():
                return number
            else:
                print(
                    f"Номер не найден или не является числом для файла: {path_str}")
        else:
            print(f"Строка не заканчивается на .html для файла: {path_str}")
    else:
        print(f"Номер не найден для файла: {path_str}")
    return None  # В случае, если номер не был найден или не соответствует условиям


def download_and_save_image(image_url, max_retries=10):
    retries = 0
    proxies = {
        "http": "http://scraperapi:6c54502fd688c7ce737f1c650444884a@proxy-server.scraperapi.com:8001",
        "https": "http://scraperapi:6c54502fd688c7ce737f1c650444884a@proxy-server.scraperapi.com:8001",
    }
    while retries < max_retries:
        try:
            # Извлекаем имя файла из URL
            image_filename = image_url.split('/')[-1]
            image_path = images_directory / image_filename
            
            # Если файл существует, возвращаем его путь
            if image_path.exists():
                logger.info(f"Image already exists: {image_filename}")
                return str(image_path)  # Преобразуем Path в строку

            # Скачиваем изображение
            response = requests.get(
                image_url,
                proxies=proxies,
                timeout=100,
                verify=False,
            )
            
            if response.status_code == 200:
                # Сохраняем в файл
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Image saved as: {image_filename}")
                return str(image_path)  # Возвращаем путь к сохраненному файлу
            else:
                logger.error(f"Failed to download image. Status code: {response.status_code}")

        except (requests.exceptions.RequestException, requests.exceptions.ReadTimeout) as retry_e:
            logger.error(f"Request error on attempt {retries + 1}: {str(retry_e)}")
            retries += 1
            if retries < max_retries:
                wait_time = 5 * retries
                logger.info(f"Waiting {wait_time} seconds before retry {retries + 1}/{max_retries}")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed")

        # Задержка между попытками
        if retries < max_retries:
            time.sleep(random.uniform(1, 3))
    
    return None  # Возвращаем None если все попытки неудачны


def save_to_excel(all_data):
    try:
        # Создаем DataFrame из списка словарей
        df = pd.DataFrame(all_data)

        # Записываем в Excel
        df.to_excel(output_file, index=False)

        logger.info(f"Data successfully saved to {output_file}")
        return output_file

    except Exception as e:
        logger.error(f"Error saving data to Excel: {e}")
        return None


if __name__ == "__main__":
    numbers = [
        51747255413,
        51767183752,
        51237242548,
        51714529627,
        51749465187
    ]
    for code in numbers:
        main_realoem(code)
    scrap()
