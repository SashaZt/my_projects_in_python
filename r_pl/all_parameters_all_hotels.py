import asyncio
import json
import os
from datetime import datetime
import aiofiles
from playwright.async_api import async_playwright


current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
all_hotels = os.path.join(temp_path, "all_hotels")

# Создание директории, если она не существует
os.makedirs(all_hotels, exist_ok=True)


async def save_response_json(json_response, i):
    """Асинхронно сохраняет JSON-данные в файл."""
    filename = os.path.join(all_hotels, f"response_page_{i}.json")
    if not os.path.exists(filename):
        async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(json_response, ensure_ascii=False, indent=4))
        print(f"Сохранён файл: {filename}")


async def log_response(response, i):
    """Логирует и сохраняет JSON-ответы от определённого URL."""
    api_url = "https://r.pl/api/bloczki/pobierz-bloczki"
    request = response.request
    if request.method == "POST" and api_url in request.url:
        try:
            json_response = await response.json()
            print(f"Получен JSON-ответ на {response.url}: {json_response}")
            # Передача данных для сохранения в файл
            # Счетчик итерации `p` будет передан из внешнего контекста
            await save_response_json(json_response, i)
        except Exception as e:
            print(f"Ошибка при получении JSON из ответа {response.url}: {e}")


async def main(url):
    timeout = 60000
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Устанавливаем обработчик для сбора и сохранения данных ответов
        def create_log_response_with_counter(i):
            async def log_response(response):
                api_url = "https://r.pl/api/bloczki/pobierz-bloczki"
                request = response.request
                if request.method == "POST" and api_url in request.url:
                    try:
                        json_response = await response.json()
                        await save_response_json(json_response, i)
                    except Exception as e:
                        print(
                            f"Ошибка при получении JSON из ответа {response.url}: {e}"
                        )

            return log_response

        # Переход на страницу, которая инициирует интересующие запросы
        response_handlers = {}  # Словарь для хранения ссылок на обработчики
        await page.goto(url)  # Замените URL на актуальный
        # Здесь нажимаем кнопку cookies
        # button_cookies = '//button[@class="r-button r-button--accent r-button--hover r-button--contained r-button--only-text r-button--svg-margin-left r-consent-buttons__button cmpboxbtnyes"]'
        await asyncio.sleep(1)
        button_xpath = "//button[contains(., 'Akceptuj wszystkie')]"
        # Дожидаемся появления кнопки с заданным текстом и кликаем по ней
        cookies_button = await page.wait_for_selector(
            f"xpath={button_xpath}", timeout=timeout
        )
        if cookies_button:
            # Кликаем по кнопке "Следующая", если она найдена
            await cookies_button.click()

        pagination_xpathr = '//div[@class="r-pagination pagination"]'
        pagination_container = await page.wait_for_selector(
            f"xpath={pagination_xpathr}", timeout=timeout
        )
        await asyncio.sleep(1)

        # Найдите все элементы по селектору
        pagination_buttons = await page.query_selector_all(
            ".r-pagination.pagination a.r-button"
        )

        # Инициализируем переменную для хранения максимального номера страницы
        last_page = 0

        for button in pagination_buttons:
            button_text = await button.text_content()
            if button_text.isdigit():
                # Преобразуем текст кнопки в число и обновляем max_page_number, если найденное число больше текущего максимума
                page_number = int(button_text)
                last_page = max(last_page, page_number)

        # Итерация по страницам
        print(last_page)
        for i in range(1, last_page + 1):
            print(i)
            # Создаем обработчик и сохраняем его в словарь
            handler = create_log_response_with_counter(i)
            response_handlers[i] = handler
            page.on("response", handler)
            # Проверяем, доступна ли кнопка "Следующая"
            next_button = await page.wait_for_selector(
                'a[class*="btn--next"]', timeout=60000
            )
            if i == 1:
                button_one = await pagination_container.query_selector(
                    "a.r-button--primary.r-pagination__page-btn:not(.r-pagination__btn--prev):not(.r-pagination__btn--next)"
                )
                if button_one:
                    await button_one.click()
                else:
                    print("Кнопка '1' не найдена.")

            elif i > 1:
                number_button_xpath = f"//a[@href[contains(.,'strona={i}')]]"
                number_button = await page.wait_for_selector(
                    f"xpath={number_button_xpath}", timeout=timeout
                )
                try:
                    # Всплывающее окно закрываем
                    button_close = await page.wait_for_selector(
                        '//div[@id="smPopupCloseButton"]', timeout=1000
                    )
                    if button_close:
                        await button_close.click()
                except Exception as e:
                    print(f"{e}")

                if number_button:
                    await number_button.click()

                await page.wait_for_load_state("networkidle")
                page.remove_listener("response", response_handlers[i - 1])
            await asyncio.sleep(5)
            if last_page in response_handlers:
                page.remove_listener("response", response_handlers[last_page])

        await browser.close()


print("Вставьте ссылку")
url = input()
asyncio.run(main(url))
