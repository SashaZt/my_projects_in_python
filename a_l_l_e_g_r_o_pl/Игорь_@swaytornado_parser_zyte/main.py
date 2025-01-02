import asyncio
import base64
from pathlib import Path

from configuration.logger_setup import logger
from zyte_api import AsyncZyteAPI

# Установка директорий
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"

html_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)


# Функция для проверки строки на корректность Base64
def is_base64(data: str) -> bool:
    """Проверяет, является ли строка корректной Base64."""
    try:
        base64.b64decode(data, validate=True)
        return True
    except Exception:
        return False


async def get_html_page(url, api_key):
    # Инициализация асинхронного клиента Zyte API
    client = AsyncZyteAPI(api_key=api_key)

    # Настройка параметров запроса
    request_params = {
        "url": url,
        "browserHtml": True,  # Указываем, что нам нужен HTML от браузера
    }

    try:
        # Отправка асинхронного запроса и получение ответа
        api_response = await client.get(request_params)

        # Проверка, что в ответе есть HTML
        if "browserHtml" in api_response:
            browser_html = api_response["browserHtml"]

            # Проверка на корректность Base64
            if is_base64(browser_html):
                # Декодирование Base64
                html_content = base64.b64decode(browser_html).decode("utf-8")
                return html_content
            else:
                logger.error(f"Некорректная строка Base64 для URL {url}")
                return "Некорректный HTML (Base64)."
        else:
            logger.error(f"Поле 'browserHtml' отсутствует для URL {url}")
            return "HTML не найден в ответе."
    except Exception as e:
        logger.error(f"Произошла ошибка при запросе для URL {url}: {str(e)}")
        return f"Произошла ошибка: {str(e)}"


async def main():
    url = "https://allegro.pl/oferta/samossaca-myjka-cisnieniowa-riwall-repw-120-l5-230-barew-alu-plyn-karcher-16998508785"  # Замените на нужный URL
    api_key = "45a471f3c80945659831851313028a78"  # Замените на ваш API ключ

    html_page = await get_html_page(url, api_key)
    name_file = url.split("/")[-1].replace("-", "_")
    html_file_path = html_files_directory / f"{name_file}.html"

    with open(
        html_file_path, "w", encoding="utf-8"
    ) as file:  # Открываем файл в текстовом режиме с указанием кодировки UTF-8
        file.write(html_page)
    logger.info(f"HTML файл сохранен: {html_file_path}")
    print(html_file_path)


if __name__ == "__main__":
    asyncio.run(main())
