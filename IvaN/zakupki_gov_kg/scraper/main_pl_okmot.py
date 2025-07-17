import asyncio
import json
import math
from pathlib import Path

from config.logger import logger
from playwright.async_api import async_playwright

current_directory = Path.cwd()
temp_directory = current_directory / "temp"
html_directory = temp_directory / "html"
temp_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)


# Функция загрузки списка прокси
def load_json():
    with open("okmot_companies.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        contract_numbers = [item["ИНН организации"] for item in data]
        return contract_numbers


async def search_and_save_contract(page, contract_number):
    """
    Ищет контракт по номеру и сохраняет HTML страницу
    """
    try:
        logger.info(f"🔍 Ищем контракт: {contract_number}")

        # Находим поле для ввода номера контракта
        input_selector = 'input[name="j_idt31"]'
        await page.wait_for_selector(input_selector, timeout=10000)

        # Очищаем поле и вводим registration_number
        await page.fill(input_selector, "")
        await page.fill(input_selector, contract_number)

        # Нажимаем кнопку "Найти"
        search_button = 'input[id="j_idt44"]'
        await page.click(search_button)

        # Ждем загрузки результатов таблицы
        await page.wait_for_selector("table.display-table.public-table", timeout=15000)
        await asyncio.sleep(1)  # Дополнительная пауза для полной загрузки

        # Проверяем, есть ли результаты в таблице
        table_rows = await page.locator("#table_data tr").count()
        if table_rows == 0:
            logger.error(f"❌ Контракт {contract_number} не найден")
            return False

        # ИСПРАВЛЕНИЕ: Ищем строку с нужным ИНН в первой колонке
        # Находим ячейку с текстом, содержащим contract_number
        inn_cell = page.locator(
            f'#table_data tr td:first-child:has-text("{contract_number}")'
        )

        if await inn_cell.count() == 0:
            logger.error(f"❌ Строка с ИНН {contract_number} не найдена")
            return False

        # Находим ссылку в той же строке (во второй колонке)
        # Получаем родительскую строку и ищем в ней ссылку
        row_with_inn = inn_cell.locator("..").first  # родительский tr элемент
        contract_link = row_with_inn.locator("td:nth-child(2) a")

        # Проверяем, существует ли ссылка
        if await contract_link.count() == 0:
            logger.error(
                f"❌ Ссылка для контракта {contract_number} не найдена в строке"
            )
            return False

        # Кликаем по ссылке контракта
        await contract_link.click()

        # Ждем загрузки страницы контракта
        await page.wait_for_load_state("networkidle", timeout=30000)

        # Получаем HTML содержимое страницы
        html_content = await page.content()

        # Сохраняем HTML файл
        file_path = html_directory / f"{contract_number}.html"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"✅ Контракт {contract_number} сохранен в {file_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при обработке контракта {contract_number}: {e}")
        return False


# async def process_contract_list(url, contract_numbers):
#     """
#     Обрабатывает список номеров контрактов
#     """
#     proxy = None
#     proxy_config = None

#     successful_contracts = []
#     failed_contracts = []

#     try:
#         async with async_playwright() as p:
#             browser = (
#                 await p.chromium.launch(proxy=proxy_config, headless=False)
#                 if proxy
#                 else await p.chromium.launch(headless=False)
#             )
#             context = await browser.new_context(accept_downloads=True)
#             page = await context.new_page()

#             # Отключаем медиа для ускорения
#             await page.route(
#                 "**/*",
#                 lambda route: (
#                     route.abort()
#                     if route.request.resource_type in ["image", "media"]
#                     else route.continue_()
#                 ),
#             )

#             # Переход на главную страницу
#             await page.goto(url, timeout=60000, wait_until="networkidle")
#             # await asyncio.sleep(1)

#             # Обрабатываем каждый контракт
#             for i, contract_number in enumerate(contract_numbers, 1):
#                 file_path = html_directory / f"{contract_number}.html"
#                 if file_path.exists():
#                     logger.info(f"📁 Файл {file_path} уже существует. Пропускаем обработку.")
#                     successful_contracts.append(contract_number)
#                     continue

#                 # Если не первый контракт, возвращаемся на главную страницу
#                 if i > 1:
#                     await page.goto(url, timeout=60000, wait_until="networkidle")
#                     # await asyncio.sleep(1)

#                 # Обрабатываем контракт
#                 success = await search_and_save_contract(page, contract_number)

#                 if success:
#                     successful_contracts.append(contract_number)
#                 else:
#                     failed_contracts.append(contract_number)


#             await browser.close()

#     except Exception as e:
#         logger.error(f"❌ Критическая ошибка: {e}")

#     if successful_contracts:
#         logger.info(f"\n✅ Успешные контракты:")


#     return successful_contracts, failed_contracts


# # Пример использования
# async def main():
#     """
#     Главная функция для запуска парсера
#     """
#     # URL страницы поиска контрактов
#     url = "http://zakupki.gov.kg/popp/view/order/centralized_procurement.xhtml"

#     # Список номеров контрактов для поиска
#     contract_numbers = load_json()

#     await process_contract_list(url, contract_numbers)

# # Запуск программы
# if __name__ == "__main__":
#     asyncio.run(main())


def check_existing_files(contract_numbers):
    """
    Проверяет какие файлы уже существуют и возвращает список недостающих
    """
    missing_contracts = []
    existing_contracts = []

    for contract_number in contract_numbers:
        file_path = html_directory / f"{contract_number}.html"
        if file_path.exists():
            existing_contracts.append(contract_number)
            logger.info(f"📁 Файл {file_path}.html уже существует")
        else:
            missing_contracts.append(contract_number)

    logger.info(f"✅ Найдено существующих файлов: {len(existing_contracts)}")
    logger.info(f"🔍 Нужно обработать: {len(missing_contracts)}")

    return missing_contracts, existing_contracts


def split_list_into_chunks(lst, num_chunks):
    """
    Разделяет список на указанное количество частей
    """
    if not lst:
        return []

    chunk_size = math.ceil(len(lst) / num_chunks)
    chunks = []

    for i in range(0, len(lst), chunk_size):
        chunk = lst[i : i + chunk_size]
        if chunk:  # Добавляем только непустые части
            chunks.append(chunk)

    return chunks


async def process_contract_thread(thread_id, url, contract_numbers):
    """
    Обрабатывает список контрактов в отдельном потоке
    """
    logger.info(
        f"🚀 Поток {thread_id}: начинаем обработку {len(contract_numbers)} контрактов"
    )

    successful_contracts = []
    failed_contracts = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            # Отключаем медиа для ускорения
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type in ["image", "media"]
                    else route.continue_()
                ),
            )

            # Переход на главную страницу
            await page.goto(url, timeout=60000, wait_until="networkidle")

            # Обрабатываем каждый контракт в этом потоке
            for i, contract_number in enumerate(contract_numbers, 1):
                logger.info(
                    f"🧵 Поток {thread_id}: обрабатываем {i}/{len(contract_numbers)} - {contract_number}"
                )

                # Если не первый контракт, возвращаемся на главную страницу
                if i > 1:
                    await page.goto(url, timeout=60000, wait_until="networkidle")

                # Обрабатываем контракт
                success = await search_and_save_contract(page, contract_number)

                if success:
                    successful_contracts.append(contract_number)
                else:
                    failed_contracts.append(contract_number)

            await browser.close()

    except Exception as e:
        logger.error(f"❌ Критическая ошибка в потоке {thread_id}: {e}")

    logger.info(
        f"✅ Поток {thread_id} завершен: успешно {len(successful_contracts)}, ошибок {len(failed_contracts)}"
    )
    return successful_contracts, failed_contracts


async def process_contract_list_multithread(url, contract_numbers, num_threads=3):
    """
    Обрабатывает список номеров контрактов в многопоточном режиме
    """
    # Проверяем существующие файлы
    missing_contracts, existing_contracts = check_existing_files(contract_numbers)

    if not missing_contracts:
        logger.info("🎉 Все файлы уже существуют! Обработка не требуется.")
        return existing_contracts, []

    # Разделяем недостающие контракты на потоки
    contract_chunks = split_list_into_chunks(missing_contracts, num_threads)
    actual_threads = len(contract_chunks)  # Реальное количество потоков

    logger.info(f"🔀 Разделено на {actual_threads} потоков:")
    for i, chunk in enumerate(contract_chunks):
        logger.info(f"   Поток {i+1}: {len(chunk)} контрактов")

    # Запускаем потоки параллельно
    tasks = []
    for thread_id, chunk in enumerate(contract_chunks, 1):
        task = asyncio.create_task(process_contract_thread(thread_id, url, chunk))
        tasks.append(task)

    # Ждем завершения всех потоков
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Собираем результаты
    all_successful = list(existing_contracts)  # Начинаем с уже существующих
    all_failed = []

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"❌ Поток {i+1} завершился с ошибкой: {result}")
            continue

        successful, failed = result
        all_successful.extend(successful)
        all_failed.extend(failed)

    # Итоговая статистика
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 ИТОГОВАЯ СТАТИСТИКА")
    logger.info(f"{'='*60}")
    logger.info(f"📁 Уже существовало: {len(existing_contracts)}")
    logger.info(
        f"✅ Успешно загружено: {len(all_successful) - len(existing_contracts)}"
    )
    logger.info(f"❌ Ошибок: {len(all_failed)}")
    logger.info(f"📊 Всего обработано: {len(all_successful)}/{len(contract_numbers)}")

    return all_successful, all_failed


# Обновленная главная функция
async def main(num_threads=5):
    """
    Главная функция для запуска многопоточного парсера
    """
    # URL страницы поиска контрактов
    url = (
        "https://zakupki.okmot.kg/popp/view/services/registry/procurementEntities.xhtml"
    )

    # Список номеров контрактов для поиска
    contract_numbers = load_json()

    logger.info(f"🚀 ЗАПУСК МНОГОПОТОЧНОГО ПАРСЕРА")
    logger.info(f"🧵 Количество потоков: {num_threads}")
    logger.info(f"📋 Всего контрактов: {len(contract_numbers)}")

    await process_contract_list_multithread(url, contract_numbers, num_threads)


# Запуск программы
if __name__ == "__main__":
    # Укажите количество потоков (по умолчанию 3)
    NUM_THREADS = 3  # Измените это значение

    asyncio.run(main(NUM_THREADS))
