import concurrent.futures
import json
import queue
import random
import sys
import threading
import time
from pathlib import Path

import pandas as pd
import requests
from loguru import logger

# Настройки
MAX_RETRIES = 10  # Максимальное количество повторных попыток
RETRY_DELAY = 5  # Пауза между повторными попытками в секундах

current_directory = Path.cwd()
json_directory = current_directory / "json"
data_directory = current_directory / "data"
log_directory = current_directory / "log"
data_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)

input_csv_file = data_directory / "output.csv"
log_file_path = log_directory / "log_message.log"
proxy_file = data_directory / "proxy.txt"  # Путь к файлу с прокси

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)

# Предполагаем, что headers определены где-то в вашем коде
headers = {
    "accept": "*/*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "origin": "https://ba.prg.kz",
    "priority": "u=1, i",
    "referer": "https://ba.prg.kz/",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
}

# Глобальный список прокси (будет доступен всем потокам)
ALL_PROXIES = []


# Функция для загрузки прокси из файла
def load_proxies():
    if not proxy_file.exists():
        logger.warning(
            f"Файл с прокси {proxy_file} не найден, используем локальное соединение"
        )
        return []

    try:
        with open(proxy_file, "r") as f:
            proxies = [line.strip() for line in f if line.strip()]

        logger.info(f"Загружено {len(proxies)} прокси из файла")
        return proxies
    except Exception as e:
        logger.error(f"Ошибка при чтении файла с прокси: {str(e)}")
        return []


# Функция для получения случайного прокси из списка
def get_random_proxy():
    if not ALL_PROXIES:
        return None
    return random.choice(ALL_PROXIES)


# Функция для чтения ID компаний из CSV файла
def read_companies_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["bin"].tolist()


# Функция получения и сохранения JSON данных с использованием прокси
def get_json(id_company, q):
    file_name = json_directory / f"{id_company}.json"

    # Если файл уже существует, пропускаем
    if file_name.exists():
        logger.warning(f"Файл для ID {id_company} уже существует, пропускаем")
        q.task_done()
        return

    retry_count = 0

    while retry_count < MAX_RETRIES:
        # Для каждой попытки выбираем случайный прокси
        proxy = get_random_proxy()
        proxies = None

        if proxy:
            proxies = {"http": proxy, "https": proxy}
            logger.debug(
                f"Используем случайный прокси {proxy} для ID {id_company} (попытка {retry_count+1})"
            )

        try:
            params = {
                "id": id_company,
                "lang": "ru",
            }

            response = requests.get(
                "https://apiba.prgapp.kz/CompanyFullInfo",
                params=params,
                headers=headers,
                proxies=proxies,
                timeout=30,
            )

            # Проверяем статус ответа
            if response.status_code == 200:
                try:
                    data = response.json()
                    with open(file_name, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    if proxy:
                        logger.info(
                            f"Успешно сохранен файл для ID {id_company} (прокси: {proxy})"
                        )
                    else:
                        logger.info(
                            f"Успешно сохранен файл для ID {id_company} (без прокси)"
                        )
                    q.task_done()
                    return
                except ValueError:
                    logger.error(f"Ошибка: ответ для ID {id_company} не содержит JSON")
            else:
                if proxy:
                    logger.error(
                        f"Ошибка для ID {id_company}: статус {response.status_code} (прокси: {proxy})"
                    )
                else:
                    logger.error(
                        f"Ошибка для ID {id_company}: статус {response.status_code} (без прокси)"
                    )

            # Если ответ не 200 или произошла ошибка парсинга JSON
            retry_count += 1
            logger.warning(
                f"Попытка {retry_count}/{MAX_RETRIES} для ID {id_company}, пауза {RETRY_DELAY} сек."
            )
            time.sleep(RETRY_DELAY)

        except requests.exceptions.RequestException as e:
            if proxy:
                logger.error(
                    f"Ошибка запроса для ID {id_company} (прокси: {proxy}): {str(e)}"
                )
            else:
                logger.error(
                    f"Ошибка запроса для ID {id_company} (без прокси): {str(e)}"
                )

            retry_count += 1
            logger.error(
                f"Попытка {retry_count}/{MAX_RETRIES} для ID {id_company}, пауза {RETRY_DELAY} сек."
            )
            time.sleep(RETRY_DELAY)

    logger.warning(f"Исчерпаны все попытки для ID {id_company}")
    q.task_done()


# Функция для работы потока
def worker(q, thread_id):
    logger.info(f"Запущен поток {thread_id}")

    while True:
        id_company = q.get()
        if id_company is None:  # Сигнал для завершения потока
            q.task_done()
            break
        get_json(id_company, q)


# Основная функция
def process_companies(num_threads=5):
    # Загружаем прокси в глобальный список
    global ALL_PROXIES
    ALL_PROXIES = load_proxies()

    if ALL_PROXIES:
        logger.info(f"Будет использовано {len(ALL_PROXIES)} разных прокси для запросов")
    else:
        logger.info("Прокси не найдены, будем использовать локальное соединение")

    # Получаем список ID компаний
    company_ids = read_companies_from_csv(input_csv_file)
    logger.info(f"Загружено {len(company_ids)} ID компаний")

    # Создаем очередь и потоки
    q = queue.Queue()
    threads = []

    # Запускаем рабочие потоки
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(q, i))
        t.daemon = True
        t.start()
        threads.append(t)

    # Добавляем ID компаний в очередь
    for id_company in company_ids:
        q.put(id_company)

    # Дожидаемся завершения обработки очереди
    q.join()

    # Останавливаем потоки
    for i in range(num_threads):
        q.put(None)

    # Дожидаемся завершения всех потоков
    for t in threads:
        t.join()

    logger.info("Обработка завершена!")


# def format_value(value):
#     if value is True:
#         return "Да"
#     elif value is False:
#         return "Нет"
#     else:
#         return value


# def process_data():
#     all_data = []
#     for json_file in json_directory.glob("*.json"):
#         with open(json_file, "r", encoding="utf-8") as file:
#             data = json.load(file)
#         company_bin = data.get("basicInfo", {}).get("bin", None)
#         isNds_raw = data.get("basicInfo", {}).get("isNds", {}).get("value", None)
#         if isNds_raw is True:
#             isNds = "Да"
#         else:
#             isNds = "Нет"
#         degreeOfRisk = (
#             data.get("basicInfo", {}).get("degreeOfRisk", {}).get("value", None)
#         )
#         egov_contacts = data.get("egovContacts", {})
#         phone_list = egov_contacts.get("phone", [])
#         phone_value = phone_list[0].get("value", None) if phone_list else None
#         gosZakupContacts = data.get("gosZakupContacts", {})
#         phone_list_goz = gosZakupContacts.get("phone", [])
#         email_list_goz = gosZakupContacts.get("email", [])
#         www_list_goz = gosZakupContacts.get("website", [])
#         phone_value_goz = (
#             phone_list_goz[0].get("value", None) if phone_list_goz else None
#         )
#         email_value_goz = (
#             email_list_goz[0].get("value", None) if email_list_goz else None
#         )
#         www_value_goz = www_list_goz[0].get("value", None) if www_list_goz else None
#         debtsInfo = data.get("debtsInfo", {})
#         kgd = debtsInfo.get("kgd", {}).get("totalDebt", None)
#         egov = debtsInfo.get("egov", {}).get("totalDebt", None)

#         reestrs = data.get("reestrs", [])

#         # Создаем пустой словарь для результатов
#         table_reestrs = {}
#         # Функция для преобразования булевых значений

#         # Проходим по каждому элементу списка
#         for item in reestrs:
#             description = item.get("description", "").replace(
#                 "Комитет государственных доходов : ", ""
#             )

#             # Приоритетные ключи для значений, в порядке предпочтения
#             priority_keys = ["isIntruder", "isNDS", "risk", "violation", "debtSumm"]

#             # Найдем первый доступный ключ
#             for key in priority_keys:
#                 if key in item:
#                     # Форматируем значение и добавляем в словарь
#                     table_reestrs[description] = format_value(item.get(key))
#                     break
#         taxes = data.get("taxes", {})
#         checkDate = taxes.get("checkDate", None)
#         taxGraph = taxes.get("taxGraph", [])
#         # Создаем словарь год: значение
#         tax_by_year = {}

#         # Годы, которые нам нужны
#         needed_years = [2021, 2022, 2023, 2024]

#         for item in taxGraph:
#             year = item.get("year")
#             value = item.get("value")
#             if year in needed_years:  # Проверяем, что год в нашем списке нужных годов
#                 tax_by_year[year] = value
#         result = {
#             "БИН": company_bin,
#             "Плательщик НДС": isNds,
#             "Степень риска налогоплательщика": degreeOfRisk,
#             "Телефон": phone_value,
#             "Телефон гоc. закупок": phone_value_goz,
#             "E-mail гоc. закупок": email_value_goz,
#             "Веб-сайт гоc. закупок": www_value_goz,
#             "Задолженность Комитет государственных доходов": kgd,
#             "Задолженность Электронное правительство": egov,
#             "Благонадежность предприятия": table_reestrs,
#             "Проверено:Комитет государственных доходов: уплата налогов": checkDate,
#             "Налоговые отчисления": tax_by_year,
#         }

#         all_data.append(result)

#     return all_data


# # Функция для преобразования вложенных словарей в плоскую структуру
# def flatten_nested_data(data_list):
#     flattened_data = []

#     for item in data_list:
#         flat_item = {}

#         # Обрабатываем простые поля
#         for key, value in item.items():
#             if not isinstance(value, dict):
#                 flat_item[key] = value

#         # Обрабатываем "Благонадежность предприятия"
#         if "Благонадежность предприятия" in item:
#             for subkey, subvalue in item["Благонадежность предприятия"].items():
#                 flat_item[f"Благонадежность_{subkey}"] = subvalue

#         # Обрабатываем "Налоговые отчисления"
#         if "Налоговые отчисления" in item:
#             for year, amount in item["Налоговые отчисления"].items():
#                 flat_item[f"Налоги_{year}"] = amount

#         flattened_data.append(flat_item)

#     return flattened_data


# def write_csv(data):
#     # Создаем DataFrame
#     df = pd.DataFrame(data)

#     # Сохраняем в CSV
#     df.to_csv("company_data.csv", index=False, encoding="utf-8")


def format_value(value):
    if value is True:
        return "Да"
    elif value is False:
        return "Нет"
    else:
        return value


def process_single_file(json_file):
    """Обрабатывает один JSON-файл и возвращает результат"""
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Проверяем, что data не None
        if data is None:
            logger.error(f"Данные в файле {json_file} отсутствуют")
            return None

        # Получаем basicInfo с дополнительной проверкой
        basicInfo = data.get("basicInfo", {})
        if basicInfo is None:
            basicInfo = {}

        company_bin = basicInfo.get("bin", None)

        # Проверка isNds
        isNds_obj = basicInfo.get("isNds")
        if isNds_obj is None:
            isNds = "Нет"
        else:
            isNds_raw = isNds_obj.get("value", None)
            if isNds_raw is True:
                isNds = "Да"
            else:
                isNds = "Нет"

        # Проверка degreeOfRisk
        degreeOfRisk_obj = basicInfo.get("degreeOfRisk")
        if degreeOfRisk_obj is None:
            degreeOfRisk = None
        else:
            degreeOfRisk = degreeOfRisk_obj.get("value", None)

        # Проверка egovContacts
        egov_contacts = data.get("egovContacts", {})
        if egov_contacts is None:
            egov_contacts = {}

        phone_list = egov_contacts.get("phone", [])
        if phone_list is None:
            phone_list = []

        phone_value = phone_list[0].get("value", None) if phone_list else None

        # Проверка gosZakupContacts
        gosZakupContacts = data.get("gosZakupContacts", {})
        if gosZakupContacts is None:
            gosZakupContacts = {}

        phone_list_goz = gosZakupContacts.get("phone", [])
        if phone_list_goz is None:
            phone_list_goz = []

        email_list_goz = gosZakupContacts.get("email", [])
        if email_list_goz is None:
            email_list_goz = []

        www_list_goz = gosZakupContacts.get("website", [])
        if www_list_goz is None:
            www_list_goz = []

        phone_value_goz = (
            phone_list_goz[0].get("value", None) if phone_list_goz else None
        )
        email_value_goz = (
            email_list_goz[0].get("value", None) if email_list_goz else None
        )
        www_value_goz = www_list_goz[0].get("value", None) if www_list_goz else None

        # Проверка debtsInfo
        debtsInfo = data.get("debtsInfo", {})
        if debtsInfo is None:
            debtsInfo = {}

        kgd_obj = debtsInfo.get("kgd", {})
        if kgd_obj is None:
            kgd_obj = {}

        egov_obj = debtsInfo.get("egov", {})
        if egov_obj is None:
            egov_obj = {}

        kgd = kgd_obj.get("totalDebt", None)
        egov = egov_obj.get("totalDebt", None)

        # Проверка reestrs
        reestrs = data.get("reestrs", [])
        if reestrs is None:
            reestrs = []

        table_reestrs = {}

        for item in reestrs:
            if item is None:
                continue

            description = item.get("description", "")
            if description is None:
                description = ""
            else:
                description = description.replace(
                    "Комитет государственных доходов : ", ""
                )

            priority_keys = ["isIntruder", "isNDS", "risk", "violation", "debtSumm"]

            for key in priority_keys:
                if key in item:
                    table_reestrs[description] = format_value(item.get(key))
                    break

        # Проверка taxes
        taxes = data.get("taxes", {})
        if taxes is None:
            taxes = {}

        checkDate = taxes.get("checkDate", None)
        taxGraph = taxes.get("taxGraph", [])
        if taxGraph is None:
            taxGraph = []

        tax_by_year = {}
        needed_years = [2021, 2022, 2023, 2024]

        for item in taxGraph:
            if item is None:
                continue

            year = item.get("year")
            value = item.get("value")
            if year in needed_years:
                tax_by_year[year] = value

        result = {
            "БИН": company_bin,
            "Плательщик НДС": isNds,
            "Степень риска налогоплательщика": degreeOfRisk,
            "Телефон": phone_value,
            "Телефон гоc. закупок": phone_value_goz,
            "E-mail гоc. закупок": email_value_goz,
            "Веб-сайт гоc. закупок": www_value_goz,
            "Задолженность Комитет государственных доходов": kgd,
            "Задолженность Электронное правительство": egov,
            "Благонадежность предприятия": table_reestrs,
            "Проверено:Комитет государственных доходов: уплата налогов": checkDate,
            "Налоговые отчисления": tax_by_year,
        }
        logger.info(f"Обработан файл {json_file}")
        return result
    except Exception as e:
        logger.warning(f"Ошибка при обработке файла {json_file}: {str(e)}")
        return None


def process_data_parallel(json_directory, max_workers=10):
    """Параллельная обработка JSON-файлов"""
    json_files = list(Path(json_directory).glob("*.json"))
    all_data = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Запускаем обработку файлов параллельно
        future_to_file = {
            executor.submit(process_single_file, file): file for file in json_files
        }

        # Собираем результаты по мере их готовности
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                result = future.result()
                if result:
                    all_data.append(result)
            except Exception as e:
                logger.warning(f"Ошибка при обработке файла {file}: {str(e)}")

    return all_data


def flatten_nested_data(data_list):
    flattened_data = []

    for item in data_list:
        flat_item = {}

        # Обрабатываем простые поля
        for key, value in item.items():
            if not isinstance(value, dict):
                flat_item[key] = value

        # Обрабатываем "Благонадежность предприятия"
        if "Благонадежность предприятия" in item:
            for subkey, subvalue in item["Благонадежность предприятия"].items():
                flat_item[f"Благонадежность_{subkey}"] = subvalue

        # Обрабатываем "Налоговые отчисления"
        if "Налоговые отчисления" in item:
            for year, amount in item["Налоговые отчисления"].items():
                flat_item[f"Налоги_{year}"] = amount

        flattened_data.append(flat_item)

    return flattened_data


def write_csv(data, output_file="company_data.csv"):
    # Создаем DataFrame
    df = pd.DataFrame(data)
    # Сохраняем в CSV
    df.to_csv(output_file, index=False, encoding="utf-8")
    logger.info(f"Данные успешно записаны в {output_file}")


def main():
    import time

    start_time = time.time()

    max_workers = 50  # Количество потоков

    logger.info(f"Начинаем обработку с использованием {max_workers} потоков...")
    data_list = process_data_parallel(json_directory, max_workers)
    logger.info(f"Обработано {len(data_list)} файлов")

    logger.info("Преобразование данных в плоскую структуру...")
    flat_data = flatten_nested_data(data_list)

    logger.info("Запись данных в CSV...")
    write_csv(flat_data)

    elapsed_time = time.time() - start_time
    logger.info(f"Задача выполнена за {elapsed_time:.2f} секунд")


# Пример использования
if __name__ == "__main__":
    # Скачиванние json
    num_threads = 50

    process_companies(num_threads)

    # Парсинг json файлов и записьв csv
    main()
