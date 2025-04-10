# src/main_pl.py
import asyncio
import json
import random
from pathlib import Path

from category_manager import category_manager
from config_utils import load_config
from logger import logger
from main_bd import get_product_data
from path_manager import get_path, is_initialized, select_category_and_init_paths
from playwright.async_api import async_playwright

BASE_URL = "https://www.eneba.com/"
# Базовая директория — текущая рабочая директория
BASE_DIR = Path(__file__).parent.parent
config = load_config()


async def run(playwright, urls):
    # Получаем пути для текущей категории
    html_product = get_path("html_product")
    json_directory = get_path("json_dir")
    category_id = get_path("category_id")
    # Проверяем валидность путей
    if not (html_product and json_directory):
        logger.error("Не удалось получить пути для сохранения файлов")
        return

    logger.info(f"Файлы HTML будут сохранены в: {html_product}")
    logger.info(f"Файлы JSON будут сохранены в: {json_directory}")

    # Запускаем браузер
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        bypass_csp=True,
        java_script_enabled=True,
        permissions=["geolocation"],
        device_scale_factor=1.0,
        has_touch=True,
        ignore_https_errors=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    )
    page = await context.new_page()

    # Обрабатываем каждый URL
    for product_slug_str in urls:
        # Очищаем данные перед обработкой новой страницы
        captured_data = []
        captured_operations = set()

        product_slug = product_slug_str["product_slug"]
        # Формируем имена файлов
        price_file = json_directory / f"{product_slug.replace('/', '_')}_price.json"
        html_file = html_product / f"{product_slug.replace('/', '_')}.html"

        # Проверяем, существуют ли оба файла
        if price_file.exists() and html_file.exists():
            logger.info(f"Файлы для {product_slug} уже существуют, пропускаем")
            continue

        # Функция для перехвата запросов
        async def handle_request(request):
            if (
                request.url == "https://www.eneba.com/graphql/"
                and request.method == "POST"
            ):
                try:
                    post_data = request.post_data
                    if post_data:
                        payload = json.loads(post_data)
                        operation_name = payload.get("operationName")
                        if (
                            operation_name == "WickedNoCache"
                        ):  # Оставляем только WickedNoCache
                            request_data = {
                                "url": request.url,
                                "method": request.method,
                                "operationName": operation_name,
                                "payload": payload,
                            }
                            request._captured_data = request_data
                except Exception as e:
                    logger.error(f"Ошибка при обработке запроса: {e}")

        # Функция для перехвата ответов
        async def handle_response(response):
            if (
                response.url == "https://www.eneba.com/graphql/"
                and response.request.method == "POST"
            ):
                try:
                    request_data = getattr(response.request, "_captured_data", None)
                    if (
                        request_data
                        and request_data["operationName"] == "WickedNoCache"
                    ):
                        response_json = await response.json()
                        captured_data.append(
                            {"request": request_data, "response": response_json}
                        )
                        captured_operations.add(request_data["operationName"])
                        logger.info(
                            f"Перехвачен ответ для: {request_data['operationName']}"
                        )
                except Exception as e:
                    logger.error(f"Ошибка при обработке ответа: {e}")

        # Подключаем обработчики
        page.on("request", handle_request)
        page.on("response", handle_response)

        # Попытка загрузки страницы с повторами
        max_retries = 5  # Максимальное количество попыток
        retry_count = 0
        page_loaded = False

        while retry_count < max_retries and not page_loaded:
            try:
                # Переходим на страницу с таймаутом
                logger.info(
                    f"Попытка {retry_count + 1}: Переход на страницу: {BASE_URL}{product_slug}"
                )
                await page.goto(
                    f"{BASE_URL}{product_slug}", timeout=60000
                )  # 60 секунд таймаут

                # Ждём, пока не получим ответ WickedNoCache
                timeout = 30
                start_time = asyncio.get_event_loop().time()
                while "WickedNoCache" not in captured_operations:
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        logger.warning(
                            f"Таймаут для {product_slug}: не удалось получить ответ WickedNoCache"
                        )
                        break
                    await asyncio.sleep(1)

                # Если получили данные, считаем страницу загруженной
                if "WickedNoCache" in captured_operations:
                    page_loaded = True
                    logger.info(
                        f"Страница для {product_slug} успешно загружена на попытке {retry_count + 1}"
                    )
                else:
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.warning(
                            f"Попытка {retry_count} не удалась. Ожидание 10 секунд перед следующей попыткой..."
                        )
                        await asyncio.sleep(
                            10
                        )  # Ждем 10 секунд перед повторной попыткой

            except Exception as e:
                retry_count += 1
                logger.error(f"Ошибка при загрузке страницы {product_slug}: {str(e)}")
                if retry_count < max_retries:
                    logger.warning(
                        f"Попытка {retry_count} не удалась. Ожидание 10 секунд перед следующей попыткой..."
                    )
                    await asyncio.sleep(10)  # Ждем 10 секунд перед повторной попыткой
                else:
                    logger.error(
                        f"Все {max_retries} попыток загрузить страницу для {product_slug} не удались"
                    )

        # Убираем обработчики перед обработкой следующего продукта
        page.remove_listener("request", handle_request)
        page.remove_listener("response", handle_response)

        # Если страница была успешно загружена, сохраняем данные
        if page_loaded:
            # Сохраняем данные в JSON-файл, если есть
            if captured_data:
                with open(price_file, "w", encoding="utf-8") as f:
                    json.dump(captured_data, f, ensure_ascii=False, indent=4)
                logger.info(
                    f"Сохранено {len(captured_data)} пар запрос-ответ в {price_file}"
                )
            else:
                logger.warning(f"Нет данных для сохранения в {price_file}")

            # Сохраняем HTML страницы
            html_content = await page.content()
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"HTML сохранён в {html_file}")
        else:
            logger.error(
                f"Не удалось загрузить страницу для {product_slug} после {max_retries} попыток"
            )

        # Случайная задержка между обработкой товаров
        delay = random.uniform(5, 10)
        logger.info(f"Случайная задержка перед следующим товаром: {delay:.2f} секунд")
        await asyncio.sleep(delay)

    # Закрываем браузер
    await browser.close()


async def main(urls):
    async with async_playwright() as playwright:
        await run(playwright, urls)


def init_category():
    """Инициализирует категорию на основе выбора пользователя"""
    categories = category_manager.get_categories()
    print("\nДоступные категории:")
    for i, (cat_id, cat_info) in enumerate(categories.items(), 1):
        print(f"{i}. {cat_info['name']} (ID: {cat_id})")

    try:
        cat_choice = int(input("\nВыберите категорию (номер): "))
        cat_keys = list(categories.keys())
        selected_category = cat_keys[cat_choice - 1]

        if not category_manager.set_current_category(selected_category):
            logger.error(f"Не удалось установить категорию {selected_category}")
            return None

        category_info = category_manager.get_current_category_info()
        logger.info(
            f"Выбрана категория: {category_info['name']} (ID: {category_info['id']})"
        )
        return category_info
    except (ValueError, IndexError):
        logger.error("Некорректный выбор категории")
        return None


if __name__ == "__main__":
    # Инициализация категории
    category_id = get_path("category_id")
    category_info = init_category()
    if not category_info:
        logger.error("Не удалось инициализировать категорию")
        exit(1)

    # Получаем данные продуктов из БД для выбранной категории

    skugs = get_product_data(category_id=category_id)

    if not skugs:
        logger.error(f"Нет данных для обработки в категории {category_id}")
        exit(1)

    logger.info(f"Найдено {len(skugs)} товаров для обработки в категории {category_id}")

    # Запускаем обработку
    asyncio.run(main(skugs))
