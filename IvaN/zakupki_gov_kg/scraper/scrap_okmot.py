import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

import aiofiles
import pandas as pd
from bs4 import BeautifulSoup
from config.logger import logger

current_directory = Path.cwd()
temp_directory = current_directory / "temp"
html_directory = temp_directory / "html"


def scrap_company_okmot():
    """
    Парсит данные компаний из HTML файлов OKMOT

    Returns:
        List[Dict]: список данных о компаниях
    """
    all_data = []
    files = list(html_directory.glob("data_*.html"))

    # Пройтись по каждому HTML файлу в папке
    for html_file in files:
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        file_name = html_file.name.replace(".html", "")
        logger.info(f"Processing file: {file_name}")

        # ИЗМЕНЕНИЕ: используем XML парсер
        soup = BeautifulSoup(content, "xml")

        # Парсим данные из таблицы
        companies = extract_companies_from_table(soup, file_name)
        all_data.extend(companies)

    logger.info(f"Всего извлечено {len(all_data)} компаний")
    return all_data


def extract_companies_from_table(
    soup: BeautifulSoup, source_file: str
) -> List[Dict[str, Any]]:
    """
    Извлекает данные компаний из XML/HTML файла

    Args:
        soup: объект BeautifulSoup
        source_file: имя исходного файла

    Returns:
        List[Dict]: список компаний
    """
    companies = []

    # Ищем CDATA содержимое в XML
    update_element = soup.find("update", id="table")
    if update_element:
        # Извлекаем содержимое CDATA
        cdata_content = update_element.string

        # ИЗМЕНЕНИЕ: парсим HTML содержимое из CDATA с HTML парсером
        html_soup = BeautifulSoup(cdata_content, "html.parser")

        # Теперь ищем строки таблицы
        rows = html_soup.find_all("tr")
        logger.info(f"Найдено {len(rows)} строк в файле {source_file}")

        for row_index, row in enumerate(rows):
            try:
                company_data = extract_company_from_row(row, source_file, row_index)
                if company_data:
                    companies.append(company_data)
            except Exception as e:
                logger.error(
                    f"Ошибка при парсинге строки {row_index} в файле {source_file}: {e}"
                )

        # Извлекаем общее количество записей из extension
        extension = soup.find("extension", {"ln": "primefaces", "type": "args"})
        if extension:
            try:
                import json as json_lib

                extension_data = json_lib.loads(extension.string)
                total_records = extension_data.get("totalRecords", 0)
                logger.info(f"Общее количество записей в системе: {total_records}")
            except Exception as e:
                logger.debug(f"Ошибка парсинга extension: {e}")

    else:
        logger.warning(f"Update элемент с table не найден в файле {source_file}")

    return companies


def extract_company_from_row(
    row: BeautifulSoup, source_file: str, row_index: int
) -> Dict[str, Any]:
    """
    Извлекает данные компании из строки таблицы

    Args:
        row: элемент tr
        source_file: имя исходного файла
        row_index: индекс строки

    Returns:
        Dict: данные компании
    """
    cells = row.find_all("td")

    if len(cells) < 5:
        logger.warning(
            f"Недостаточно ячеек в строке {row_index} файла {source_file}: {len(cells)}"
        )
        return {}

    # Извлекаем данные из ячеек
    company_data = {
        "registration_number": clean_text(cells[0].get_text(strip=True)),
        "company_name": extract_company_name(cells[1]),
        "company_type": clean_text(cells[2].get_text(strip=True)),
        "status": clean_text(cells[3].get_text(strip=True)),
        "registration_date": clean_text(cells[4].get_text(strip=True)),
    }

    # Дополнительные атрибуты строки
    data_ri = row.get("data-ri")
    data_rk = row.get("data-rk")

    if data_ri:
        company_data["data_ri"] = data_ri
    if data_rk:
        company_data["data_rk"] = data_rk

    return company_data


def extract_company_name(cell) -> str:
    """
    Извлекает название компании из ячейки (может содержать ссылку)

    Args:
        cell: ячейка таблицы

    Returns:
        str: название компании
    """
    # Проверяем наличие ссылки
    link = cell.find("a")
    if link:
        return clean_text(link.get_text(strip=True))
    else:
        return clean_text(cell.get_text(strip=True))


def clean_text(text: str) -> str:
    """
    Очищает текст от лишних символов

    Args:
        text: исходный текст

    Returns:
        str: очищенный текст
    """
    if not text:
        return ""

    # Убираем неразрывные пробелы и лишние пробелы
    cleaned = text.replace("\xa0", " ").strip()
    # Убираем множественные пробелы
    cleaned = " ".join(cleaned.split())

    return cleaned


async def save_okmot_data_to_json(
    companies: List[Dict[str, Any]], filename: str = "okmot_companies.json"
):
    """
    Асинхронно сохраняет данные OKMOT в JSON

    Args:
        companies: список компаний
        filename: имя файла
    """
    try:
        # data = {
        #     "companies": companies,
        # }

        async with aiofiles.open(filename, "w", encoding="utf-8") as f:
            await f.write(json.dumps(companies, ensure_ascii=False, indent=4))

        logger.info(f"Данные OKMOT о {len(companies)} компаниях сохранены в {filename}")

    except Exception as e:
        logger.error(f"Ошибка при сохранении JSON: {e}")
        raise


def save_okmot_data_to_excel(
    companies: List[Dict[str, Any]], filename: str = "okmot_companies.xlsx"
):
    """
    Сохраняет данные OKMOT в Excel

    Args:
        companies: список компаний
        filename: имя файла
    """
    try:
        df = pd.DataFrame(companies)

        # Переименовываем колонки на русский
        column_mapping = {
            "registration_number": "Регистрационный номер",
            "company_name": "Наименование компании",
            "company_type": "Тип компании",
            "status": "Статус",
            "registration_date": "Дата регистрации",
            "source_file": "Исходный файл",
            "row_index": "Индекс строки",
            "data_ri": "Data RI",
            "data_rk": "Data RK",
        }

        # Упорядочиваем колонки
        desired_order = [
            "registration_number",
            "company_name",
            "company_type",
            "status",
            "registration_date",
            "source_file",
        ]

        existing_columns = [col for col in desired_order if col in df.columns]
        other_columns = [col for col in df.columns if col not in desired_order]
        df = df[existing_columns + other_columns]

        df = df.rename(columns=column_mapping)

        # Сохраняем в Excel
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Компании OKMOT", index=False)

            # Статистика
            stats_df = pd.DataFrame(
                [
                    ["Всего компаний", len(companies)],
                    ["Уникальных статусов", df["Статус"].nunique()],
                    ["Активных компаний", len(df[df["Статус"] == "Активный"])],
                    ["Дата создания отчета", "2025-07-10"],
                ],
                columns=["Показатель", "Значение"],
            )

            stats_df.to_excel(writer, sheet_name="Статистика", index=False)

        logger.info(f"Excel файл OKMOT сохранен: {filename}")
        return filename

    except Exception as e:
        logger.error(f"Ошибка при создании Excel OKMOT: {e}")
        raise


async def main_okmot_scraping():
    """
    Основная функция для парсинга данных OKMOT
    """
    try:
        # Парсим данные
        companies = scrap_company_okmot()

        if not companies:
            logger.warning("Данные компаний OKMOT не найдены")
            return

        # Сохраняем в JSON
        await save_okmot_data_to_json(companies)

        # Сохраняем в Excel
        excel_file = save_okmot_data_to_excel(companies)

        # Статистика
        logger.info("=== СТАТИСТИКА OKMOT ===")
        logger.info(f"Всего компаний: {len(companies)}")

        # Подсчет по статусам
        statuses = {}
        for company in companies:
            status = company.get("status", "Неизвестно")
            statuses[status] = statuses.get(status, 0) + 1

        logger.info("Распределение по статусам:")
        for status, count in statuses.items():
            logger.info(f"  {status}: {count}")

        return companies

    except Exception as e:
        logger.error(f"Ошибка в парсинге OKMOT: {e}")
        raise


def process_all_html_files():
    """
    Обрабатывает все HTML файлы из директории html_directory
    """
    # Ищем все HTML файлы
    files = list(html_directory.glob("*.html"))
    print(f"Найдено {len(files)} файлов для обработки")
    all_organizations = []
    successful_files = 0
    total_records = 0

    for file_path in files:
        try:
            # Читаем файл
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Извлекаем данные об организации
            organizations = extract_organization_from_html(content)

            if organizations:
                all_organizations.extend(organizations)
                successful_files += 1
                total_records += len(organizations)
                logger.info(
                    f"Обработан файл {file_path}: найдено {len(organizations)} записей"
                )
            else:
                logger.error(f"    ✗ Записи не найдены в файле {file_path}")

        except Exception as e:
            logger.error(f"    ✗ Ошибка при обработке файла {file_path}: {e}")
            continue

    # Сохраняем все данные в JSON
    if all_organizations:
        save_to_json(all_organizations, "organization_data.json")

    logger.info(
        f"Обработано файлов: {successful_files}, найдено записей: {total_records}"
    )
    return all_organizations


def extract_organization_from_html(file_content):
    """
    Извлекает данные об организации из HTML файла
    """
    try:
        # Парсим HTML
        soup = BeautifulSoup(file_content, "lxml")

        # Ищем таблицу с id="j_idt35"
        table = soup.find("table", id="j_idt35")
        if not table:
            logger.error("    ✗ Не найдена таблица <table id='j_idt35'>")
            return []

        # Извлекаем строки таблицы
        rows = table.find_all("tr")
        if not rows:
            logger.error("    ✗ Таблица пуста")
            return []

        organization = {}
        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 2:  # Ожидаем 2 ячейки: заголовок и значение
                header = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)

                # Если в ячейке есть ссылка, извлекаем её текст
                link = cells[1].find("a")
                if link:
                    value = link.get_text(strip=True)

                # Очищаем лишние пробелы
                value = " ".join(value.split())
                organization[header] = value

        # Проверяем, что словарь не пустой
        if organization:
            return [organization]
        else:
            logger.error("    ✗ Данные об организации не найдены")
            return []

    except Exception as e:
        logger.error(f"    ✗ Ошибка при парсинге HTML: {e}")
        return []


def save_to_json(data, filename="organization_data.json"):
    """
    Сохраняет данные в JSON файл
    """
    if not data:
        logger.error("Нет данных для сохранения")
        return False

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"✓ Сохранено {len(data)} записей в файл {filename}")
        return True
    except Exception as e:
        logger.error(f"✗ Ошибка при сохранении: {e}")
        return False


# Для запуска
if __name__ == "__main__":
    # asyncio.run(main_okmot_scraping())
    process_all_html_files()
