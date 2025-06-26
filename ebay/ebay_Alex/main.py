import argparse
import concurrent.futures
import json
import random
import re
import time
from pathlib import Path
from threading import Lock

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup
from config.logger import logger
from requests.exceptions import HTTPError
from scrap import scrap_online
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Инициализация директорий
current_directory = Path.cwd()
data_directory = current_directory / "data"
config_directory = current_directory / "config"
progress_directory = current_directory / "progress"
temp_directory = current_directory / "temp"
xlsx_directory = temp_directory / "xlsx"
json_directory = temp_directory / "json"

html_directory = temp_directory / "html"
config_directory = current_directory / "config"
temp_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)


config_file = config_directory / "config.json"

# Заголовки HTTP-запросов
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "priority": "u=0, i",
    "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-full-version": '"135.0.7049.115"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"19.0.0"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
}
# Глобальный список прокси
proxy_list = []


def load_proxies():
    """Загружает список прокси-серверов из config.json"""
    global proxy_list
    try:
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                if "proxy_server" in config and isinstance(
                    config["proxy_server"], list
                ):
                    proxy_list = config["proxy_server"]
                    logger.info(
                        f"Загружено {len(proxy_list)} прокси-серверов из config.json"
                    )
                else:
                    logger.warning("В config.json отсутствует список прокси-серверов")
        else:
            logger.warning("Файл config.json не найден")
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации прокси: {str(e)}")


def get_random_proxy():
    """Возвращает случайный прокси из списка"""
    if not proxy_list:
        return None
    proxy_url = random.choice(proxy_list)
    proxy_url = proxy_url.strip()
    return {"http": proxy_url, "https": proxy_url}


@retry(
    stop=stop_after_attempt(10),
    wait=wait_fixed(10),
    retry=retry_if_exception_type(
        (HTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout)
    ),
)
def make_request(url):
    """Выполняет HTTP-запрос"""
    try:
        proxies = get_random_proxy()
        response = requests.get(
            url,
            # cook/ies=cookies,
            proxies=proxies,
            headers=headers,
            timeout=30,
            verify=False,
        )
        response.raise_for_status()
        return response.text
    except requests.exceptions.ProxyError as e:
        logger.error(f"❌ Ошибка прокси для {url}: {e}")
        raise

    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Ошибка соединения {url}: {e}")
        raise

    except requests.exceptions.Timeout as e:
        logger.error(f"❌ Таймаут запроса {url}: {e}")
        raise

    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP ошибка {url}: {e}")
        raise

    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка запроса {url}: {e}")
        raise


def make_soup(html_content):
    """Создает BeautifulSoup объект"""
    return BeautifulSoup(html_content, "lxml")


def extract_filter_options(soup, filter_name):
    """Извлекает опции для указанного фильтра"""
    options = []
    try:
        table = soup.find("section", attrs={"id": "brw-refinement-root"})
        filter_containers = table.find_all("span", class_="filter-menu-button")

        target_container = None
        for container in filter_containers:
            filter_label = container.find("span", class_="filter-label")
            if filter_label and filter_label.get_text().strip() == filter_name:
                target_container = container
                break

        if not target_container:
            logger.warning(f"⚠️  Фильтр '{filter_name}' не найден")
            return options

        option_items = target_container.find_all("li", class_="brwr__inputs")
        logger.info(f"📋 Найдено {len(option_items)} опций для фильтра '{filter_name}'")

        for item in option_items:
            link = item.find("a", class_="brwr__inputs__actions")
            if not link:
                continue

            href = link.get("href")
            if not href:
                continue

            option_span = link.find("span", class_="textual-display")
            if not option_span:
                continue

            option_name = option_span.get_text().strip()
            clean_url = href.replace("&amp;", "&")

            options.append({"name": option_name, "url": clean_url})

        return options
    except Exception as e:
        logger.error(f"❌ Ошибка при извлечении фильтра '{filter_name}': {e}")
        return []


def get_results_count(soup):
    """Извлекает количество результатов со страницы"""
    try:
        count_element = soup.find("h2", class_="textual-display brw-controls__count")

        if not count_element:
            count_element = soup.find("span", class_="brw-controls__count")

        if count_element:
            count_text = count_element.get_text()
            match = re.search(r"([\d,]+)", count_text)
            if match:
                count_str = match.group(1).replace(",", "")
                count = int(count_str)
                return count

        return 0
    except Exception as e:
        logger.error(f"❌ Ошибка при извлечении количества: {e}")
        return 0


def get_final_segment_urls(url, applied_filters=None, max_results=10000):
    """
    Рекурсивно разбивает URL на сегменты ≤ max_results
    Создает папки для брендов

    Args:
        url (str): URL для проверки
        applied_filters (list): Уже примененные фильтры
        max_results (int): Максимальное количество результатов в сегменте

    Yields:
        tuple: (url, name) - Финальные URL с товарами и название бренда
    """
    if applied_filters is None:
        applied_filters = []

    filter_path = " → ".join(applied_filters) if applied_filters else "Базовая страница"
    logger.info(f"🔍 Проверяем: {filter_path}")

    # Загружаем страницу
    response_text = make_request(url)
    if not response_text:
        return

    soup = make_soup(response_text)
    count = get_results_count(soup)

    logger.info(f"📊 Результатов: {count:,}")

    # Если результатов приемлемо - возвращаем URL с информацией о бренде
    if count <= max_results:
        logger.info(f"✅ Готовый сегмент: {count:,} результатов")

        # Определяем бренд из примененных фильтров
        name = "no_brand"
        for filter_item in applied_filters:
            if filter_item.startswith("Brand: "):
                brand_name = filter_item.replace("Brand: ", "").strip()
                # Очищаем имя бренда от недопустимых символов для папки
                brand_name = re.sub(r'[<>:"/\\|?*]', "_", brand_name)
                break

        yield url, brand_name
        return

    # Применяем дополнительную фильтрацию
    logger.info(
        f"⚠️  Много результатов ({count:,} > {max_results:,}). Применяем фильтрацию."
    )

    filters_sequence = [
        "Brand",
        "Condition",
        "Price",
        "Type",
        "Brand Type",
        "Programming Required",
        "Country/Region of Manufacture",
    ]

    # Находим следующий фильтр
    next_filter = None
    for filter_name in filters_sequence:
        if not any(filter_name in af for af in applied_filters):
            next_filter = filter_name
            break

    if not next_filter:
        logger.warning(
            f"⚠️  Все фильтры применены, но результатов {count:,}. Возвращаем как есть."
        )

        # Определяем бренд из примененных фильтров
        brand_name = "no_brand"
        for filter_item in applied_filters:
            if filter_item.startswith("Brand: "):
                brand_name = filter_item.replace("Brand: ", "").strip()
                brand_name = re.sub(r'[<>:"/\\|?*]', "_", brand_name)
                break

        yield url, brand_name
        return

    logger.info(f"🎯 Применяем фильтр: {next_filter}")

    # Извлекаем опции фильтра
    filter_options = extract_filter_options(soup, next_filter)

    if not filter_options:
        logger.error(f"❌ Не удалось извлечь опции для '{next_filter}'")

        # Определяем бренд из примененных фильтров
        brand_name = "no_brand"
        for filter_item in applied_filters:
            if filter_item.startswith("Brand: "):
                brand_name = filter_item.replace("Brand: ", "").strip()
                brand_name = re.sub(r'[<>:"/\\|?*]', "_", brand_name)
                break

        yield url, brand_name
        return

    # Рекурсивно обрабатываем каждую опцию
    for i, option in enumerate(filter_options):
        option_name = option["name"]
        option_url = option["url"]

        logger.info(f"📌 Опция {i+1}/{len(filter_options)}: {option_name}")

        new_applied_filters = applied_filters + [f"{next_filter}: {option_name}"]

        # Рекурсивно получаем URL из этой опции
        yield from get_final_segment_urls(option_url, new_applied_filters, max_results)


def scrape_page(full_url, params=None):
    """
    Обрабатывает одну страницу и извлекает ссылки на товары

    Args:
        url (str): Базовый URL страницы
        params (dict): Параметры запроса

    Returns:
        tuple: (next_url, page_hrefs) - URL следующей страницы и список найденных ссылок
    """
    page_hrefs = []

    try:

        logger.info(f"Запрашиваем: {full_url}")

        # Выполняем запрос
        src = make_request(full_url)
        soup = BeautifulSoup(src, "lxml")

        # Ищем структурированные данные JSON-LD
        json_ld_scripts = soup.find_all("script", {"type": "application/ld+json"})

        # Обрабатываем каждый блок JSON-LD
        for script in json_ld_scripts:
            try:
                # Извлекаем JSON-данные из тега script
                json_data = json.loads(script.string)

                # Проверяем, есть ли данные о товарах
                if (
                    "about" in json_data
                    and "offers" in json_data["about"]
                    and "itemOffered" in json_data["about"]["offers"]
                ):
                    # Извлекаем список товаров
                    items = json_data["about"]["offers"]["itemOffered"]

                    # Перебираем товары и извлекаем URL
                    for item in items:
                        if "url" in item:
                            # Очищаем URL от параметров отслеживания, если необходимо
                            item_url = item["url"]
                            if "?" in item_url:
                                cleaned_url = item_url.split("?")[0]
                                page_hrefs.append(cleaned_url)
                            else:
                                page_hrefs.append(item_url)
            except json.JSONDecodeError:
                logger.warning("Не удалось разобрать JSON-LD")
                continue
            except Exception as e:
                logger.warning(f"Ошибка при обработке JSON-LD: {str(e)}")
                continue

        # Проверяем наличие следующей страницы
        next_button = soup.select_one("a.pagination__next")

        # Проверяем, что кнопка существует, имеет атрибут href и не отключена
        if next_button and "href" in next_button.attrs:
            disabled_next = soup.select_one('a.pagination__next[aria-disabled="true"]')

            if not disabled_next:
                next_url = next_button["href"]
                logger.info(f"Найдена ссылка на следующую страницу: {next_url}")
                return next_url, page_hrefs

        return None, page_hrefs
    except Exception as e:
        logger.error(f"Ошибка при обработке {full_url}: {str(e)}")
        return None, []


def collect_segment_urls(base_url, threads, max_results=10000):
    """
    Собирает все финальные URL сегментов и обрабатывает их по одному
    Создает папки для брендов

    Args:
        base_url (str): Базовый URL eBay
        max_results (int): Максимальное количество результатов в сегменте
    """
    logger.info("🚀 НАЧИНАЕМ СБОР И ОБРАБОТКУ СЕГМЕНТОВ")
    logger.info("=" * 60)
    logger.info(f"🎯 Цель: URL с товарами ≤ {max_results:,}")
    logger.info("=" * 60)

    segment_counter = 0

    # Обрабатываем каждый URL сразу как только получаем его из генератора
    for segment_url, brand_name in get_final_segment_urls(
        base_url, max_results=max_results
    ):
        segment_counter += 1
        logger.info(
            f"🔗 Получен сегмент #{segment_counter} для бренда '{brand_name}': {segment_url}"
        )

        # Создаем папку для бренда
        brand_directory = json_directory / brand_name
        brand_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Создана/проверена папка: {brand_directory}")

        # Обрабатываем сегмент сразу
        success = process_single_segment(
            segment_url, segment_counter, brand_name, brand_directory, threads
        )
        if success:
            logger.info(f"✅ ГОТОВО! Обработано {segment_counter} сегментов")
            break


def process_single_segment(
    segment_url, segment_number, brand_name, brand_directory, threads
):
    """
    Обрабатывает один сегмент - добавляет пагинацию и собирает товары

    Args:
        segment_url (str): URL сегмента
        segment_number (int): Номер сегмента для логирования
        brand_name (str): Название бренда
        brand_directory (Path): Путь к папке бренда
        threads (int): Количество потоков для загрузки товаров
    """
    logger.info(f"🔄 ОБРАБОТКА СЕГМЕНТА #{segment_number}")
    logger.info(f"📌 URL: {segment_url}")

    total_processed_urls = 0
    total_processed_pages = 0
    current_page = 1
    next_url = None

    # Цикл по страницам текущего сегмента
    while True:
        logger.info(f"📄 Сегмент #{segment_number} | Страница {current_page}")

        # Определяем URL для текущей страницы
        if current_page == 1:
            # Первая страница - используем базовый URL сегмента
            page_url = segment_url
            next_url, page_hrefs = scrape_page(page_url)
        else:
            # Последующие страницы
            if next_url is None:
                # Если нет прямой ссылки, формируем URL с параметром пагинации
                separator = "&" if "?" in segment_url else "?"
                page_url = f"{segment_url}{separator}_pgn={current_page}"
                if "rt=nc" not in page_url:
                    page_url += "&rt=nc"
                next_url, page_hrefs = scrape_page(page_url)
            else:
                # Используем прямую ссылку на следующую страницу
                next_url, page_hrefs = scrape_page(next_url)

        # Увеличиваем счетчик обработанных страниц
        total_processed_pages += 1

        # Обрабатываем найденные товары
        if page_hrefs:
            logger.info(
                f"✅ Найдено {len(page_hrefs)} товаров на странице {current_page}"
            )

            # Запускаем многопоточную загрузку страниц товаров
            try:
                success_count = get_product_th(
                    page_hrefs, brand_directory, threads=threads
                )
                total_processed_urls += success_count

                logger.info(f"📥 Загружено {success_count}/{len(page_hrefs)} товаров")
                logger.info(
                    f"📊 Сегмент #{segment_number} | Всего: {total_processed_urls} товаров, {total_processed_pages} страниц"
                )

            except Exception as e:
                logger.error(f"❌ Ошибка при загрузке товаров: {e}")
        else:
            logger.warning(f"⚠️ На странице {current_page} не найдено товаров")

        # Проверяем, есть ли следующая страница
        if next_url:
            current_page += 1

        else:
            logger.info(
                f"🏁 Сегмент #{segment_number} завершен | {total_processed_pages} страниц | {total_processed_urls} товаров"
            )
            break

    return {
        "segment_number": segment_number,
        "brand_name": brand_name,
        "total_pages": total_processed_pages,
        "total_products": total_processed_urls,
    }


def get_product_th(urls, brand_directory, threads):
    """
    Загружает страницы товаров в параллельном режиме.
    Ведет учет обработанных URL и пропускает только успешно загруженные.
    Повторно обрабатывает URL со статусами 'failed' и 'error'.

    Args:
        urls (list): Список URL для загрузки
        brand_directory (Path): Папка бренда для сохранения
        threads (int): Количество потоков для параллельной загрузки. По умолчанию 40.

    Returns:
        int: Количество успешно загруженных страниц
    """
    # Проверяем список URL
    if not urls:
        logger.warning("Список URL пуст")
        return 0

    total_urls = len(urls)
    logger.info(f"Начинаем загрузку {total_urls} страниц товаров")

    # Файл для хранения маппинга обработанных URL
    mapping_file = brand_directory / "processed_urls.csv"

    # Загружаем уже обработанные URL из файла
    processed_urls_success = set()  # Только успешно обработанные
    processed_urls_data = {}  # Данные обо всех обработанных URL

    if mapping_file.exists():
        try:
            existing_df = pd.read_csv(mapping_file)
            if "url" in existing_df.columns:
                for _, row in existing_df.iterrows():
                    url = row["url"]
                    status = row.get("status", "unknown")

                    # Сохраняем данные о URL
                    processed_urls_data[url] = {
                        "status": status,
                        "timestamp": row.get("timestamp", ""),
                        "error": row.get("error", ""),
                    }

                    # Только успешные URL добавляем в set для пропуска
                    if status == "success":
                        processed_urls_success.add(url)
                # count_urls = int(len(processed_urls_data))
                # count_urls_success = int(len(processed_urls_success))
                difference_threshold = 5

                logger.info(
                    f"📋 Загружено {len(processed_urls_data)} записей из {mapping_file.name}"
                )
                logger.info(f"✅ Из них успешных: {len(processed_urls_success)}")
                # difference = abs(count_urls - count_urls_success)
                # if difference <= difference_threshold:
                #     logger.info("Все скачали")
                #     exit()
                # Считаем количество неудачных для повторной обработки
                failed_count = sum(
                    1
                    for data in processed_urls_data.values()
                    if data["status"] in ["failed", "error"]
                )
                if failed_count > 0:
                    logger.info(
                        f"🔄 К повторной обработке: {failed_count} неудачных URL"
                    )

        except Exception as e:
            logger.warning(f"⚠️ Ошибка при загрузке файла маппинга: {e}")
            processed_urls_success = set()
            processed_urls_data = {}

    # Фильтруем URL - исключаем только те, что успешно обработаны
    urls_to_process = []
    retry_urls = []

    for url in urls:
        if url in processed_urls_success:
            continue  # Пропускаем успешно обработанные
        elif url in processed_urls_data:
            # URL есть в базе, но статус не 'success' - добавляем для повторной обработки
            retry_urls.append(url)
            urls_to_process.append(url)
        else:
            # Новый URL
            urls_to_process.append(url)

    skipped_count = len(urls) - len(urls_to_process)

    if skipped_count > 0:
        logger.info(f"⏭️ Пропускаем {skipped_count} успешно обработанных URL")

    if retry_urls:
        logger.info(f"🔄 Повторная обработка {len(retry_urls)} неудачных URL")

    if not urls_to_process:
        logger.info("✅ Все URL уже успешно обработаны, пропускаем")
        return 0

    logger.info(
        f"🔄 К обработке: {len(urls_to_process)} URL ({len(urls_to_process) - len(retry_urls)} новых + {len(retry_urls)} повторных)"
    )

    # Список для хранения обработанных URL
    newly_processed_urls = []

    # Блокировки для безопасного доступа
    processed_lock = Lock()
    log_lock = Lock()

    # Счетчик обработанных URL
    processed_counter = {"count": 0}
    counter_lock = Lock()

    # Определяем функцию для обработки одного URL
    def process_url(url):
        try:
            # Двойная проверка - возможно URL был обработан в другом потоке
            with processed_lock:
                if url in processed_urls_success:
                    return False

            # Выполняем запрос
            src = make_request(url)

            # Обрабатываем товар
            result = scrap_online(src, brand_directory)

            if result:
                # URL успешно обработан
                with processed_lock:
                    newly_processed_urls.append(
                        {
                            "url": url,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "success",
                        }
                    )
                    processed_urls_success.add(url)  # Добавляем в set успешных

                    # Если это повторная обработка, логируем обновление статуса
                    if (
                        url in processed_urls_data
                        and processed_urls_data[url]["status"] != "success"
                    ):
                        old_status = processed_urls_data[url]["status"]
                        logger.info(
                            f"🔄 URL {url} - статус изменен с '{old_status}' на 'success'"
                        )

                # Увеличиваем счетчик обработанных URL
                with counter_lock:
                    processed_counter["count"] += 1
                    count = processed_counter["count"]

                    # Периодически сохраняем маппинг
                    if count % 50 == 0:  # Сохраняем каждые 50 URL
                        save_processed_urls(
                            mapping_file, newly_processed_urls, processed_lock
                        )
                        logger.info(
                            f"💾 Промежуточное сохранение: {count}/{len(urls_to_process)} обработано"
                        )

                return True
            else:
                # Неудачная обработка
                with processed_lock:
                    newly_processed_urls.append(
                        {
                            "url": url,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "failed",
                        }
                    )
                return False

        except Exception as e:
            with log_lock:
                logger.error(f"❌ Ошибка при загрузке {url}: {str(e)}")

            # Записываем ошибку
            with processed_lock:
                newly_processed_urls.append(
                    {
                        "url": url,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "error",
                        "error": str(e),
                    }
                )
            return False

    # Запускаем многопоточную обработку
    start_time = time.time()
    logger.info(f"🚀 Запуск загрузки в {threads} потоков")

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        results = list(executor.map(process_url, urls_to_process))

    # Сохраняем финальный маппинг
    save_processed_urls(mapping_file, newly_processed_urls, processed_lock)

    end_time = time.time()
    total_time = end_time - start_time
    success_count = sum(1 for r in results if r)

    logger.info(
        f"✅ Загрузка завершена: {success_count}/{len(urls_to_process)} успешно"
    )
    logger.info(f"⏱️ Затраченное время: {total_time:.2f} секунд")
    logger.info(f"📊 Всего успешных в базе: {len(processed_urls_success)} URL")

    return success_count


def save_processed_urls(mapping_file, newly_processed_urls, lock):
    """
    Сохраняет список обработанных URL в CSV файл
    Обновляет существующие записи или добавляет новые

    Args:
        mapping_file (Path): Путь к файлу маппинга
        newly_processed_urls (list): Список новых/обновленных URL
        lock (Lock): Блокировка для безопасного доступа
    """
    try:
        with lock:
            if not newly_processed_urls:
                return

            # Создаем DataFrame из новых URL
            new_df = pd.DataFrame(newly_processed_urls)

            # Если файл существует, загружаем существующие данные
            if mapping_file.exists():
                try:
                    existing_df = pd.read_csv(mapping_file)

                    # Объединяем данные
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)

                    # Удаляем дубликаты по URL, оставляя последнюю запись (самую свежую)
                    combined_df = combined_df.drop_duplicates(
                        subset=["url"], keep="last"
                    )

                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при чтении существующего файла: {e}")
                    combined_df = new_df
            else:
                combined_df = new_df

            # Сохраняем в файл
            combined_df.to_csv(mapping_file, index=False)
            logger.debug(
                f"💾 Сохранено {len(combined_df)} записей в {mapping_file.name}"
            )

            # Очищаем список после сохранения
            newly_processed_urls.clear()

    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении маппинга: {e}")


def main(base_url, threads):
    """Основная функция"""
    # Загружаем прокси
    load_proxies()

    try:
        # Собираем и обрабатываем сегменты по одному
        collect_segment_urls(base_url, threads, max_results=10000)

        logger.info("🎉 ВСЯ ОБРАБОТКА ЗАВЕРШЕНА!")
        return False
    except KeyboardInterrupt:
        logger.info("⏹️  Процесс прерван пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    # Настройка аргументов командной строки
    parser = argparse.ArgumentParser(description="Скрипт для обработки URL eBay")
    parser.add_argument(
        "--base_url",
        type=str,
        default="https://www.ebay.com",
        help="Базовый URL для обработки",
    )
    parser.add_argument("--threads", type=int, default=1, help="Количество потоков")
    parser.add_argument("--count", type=int, default=1, help="Количество попыток")

    args = parser.parse_args()

    # Валидация аргументов
    if args.threads <= 0:
        parser.error("Количество потоков должно быть положительным числом")
    if args.count <= 0:
        parser.error("Количество попыток должно быть положительным числом")

    # Запуск основной функции
    count = 0
    while count < args.count:
        try:
            logger.info(f"Попытка {count + 1} из {args.count}")
            if main(args.base_url, args.threads):
                logger.info("✅ Успешное выполнение, завершение работы")
                break
            count += 1
        except Exception as e:
            logger.error(f"❌ Ошибка в основном цикле: {e}")
            logger.info("🔄 Повторная попытка через 10 секунд...")
            time.sleep(10)
    else:
        logger.info(f"🛑 Достигнуто максимальное количество попыток ({args.count})")
