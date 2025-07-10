import asyncio
import base64
import hashlib
import json
import random
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import pandas as pd
from curl_cffi.requests import AsyncSession
from path_manager import get_path
from rozetka_path_manager import (
    get_rozetka_path,
    select_rozetka_category_and_init_paths,
)

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent  # из src/ поднимаемся на уровень выше
sys.path.insert(0, str(project_root))

from config import Config, logger

EUROPEAN_COUNTRIES = [
    "eu",
    "at",
    "be",
    "bg",
    "hr",
    "cy",
    "cz",
    "dk",
    "ee",
    "fi",
    "fr",
    "de",
    "gr",
    "hu",
    "is",
    "ie",
    "it",
    "lv",
    "li",
    "lt",
    "mt",
    "nl",
    "no",
    "pl",
    "pt",
    "ro",
    "sk",
    "si",
    "es",
    "se",
    "ch",
    "uk",
    "ua",
]


def get_random_european_country():
    """Получить случайную европейскую страну"""
    return random.choice(EUROPEAN_COUNTRIES)


def add_country_to_proxy(base_proxy: str, country: str = None) -> str:
    """
    Добавить country_code к ScraperAPI прокси

    Args:
        base_proxy: Базовый прокси (http://scraperapi:API_KEY@proxy-server.scraperapi.com:8001)
        country: Код страны (если None, выберется случайная европейская)

    Returns:
        Прокси с геотаргетингом
    """
    if country is None:
        country = get_random_european_country()

    ukraine_headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "cookie": "region=ukraine; exchange=UAH; lng=en; scm=d.ukraine.863729e3fa631fa4.158369ef0c4e580bf49c7c670cec466f7907e3870836464ee07890d96912a875",
    }

    # Кодируем заголовки
    headers_json = json.dumps(ukraine_headers)
    headers_encoded = base64.b64encode(headers_json.encode()).decode()

    # Создаем прокси с заголовками
    modified_proxy = base_proxy.replace(
        "scraperapi:",
        f"scraperapi.country_code={country}.keep_headers=true.custom_headers={headers_encoded}:",
    )

    return modified_proxy


class Downloader:
    """
    Продвинутый HTTP клиент с TLS fingerprinting для обхода блокировок

    Особенности:
    - Эмуляция различных браузеров (Chrome, Firefox, Safari, Edge)
    - Поддержка прокси (опционально)
    - Контроль количества одновременных запросов
    - Автоматические повторы при ошибках
    - Случайные задержки между запросами
    - Ротация User-Agent'ов
    """

    def __init__(self, config: Config, proxy: Optional[str] = None):
        """
        Инициализация загрузчика

        Args:
            config: Объект конфигурации Config
            proxy: Прокси в формате "http://user:pass@host:port" или None (по умолчанию берется из config)
        """
        self.config = config.client

        # Прокси: если передан явно - используем его, иначе из конфига, иначе None
        if proxy is not None:
            self.proxy = proxy
        elif self.config.proxy:
            self.proxy = self.config.proxy
        else:
            self.proxy = None

        self.semaphore = asyncio.Semaphore(self.config.max_workers)
        self.session_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retry_attempts": 0,
        }

        # Создаем директорию для загрузок из конфига
        # self.output_path = paths.html

        # Используем глобальный логгер
        self.logger = logger

    def _get_filename_from_url(self, url: str) -> str:
        """Генерировать имя файла на основе URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return f"{url_hash}.html"

    def is_russia_blocked(self, content):
        """Проверяет блокировку России"""
        if not content:
            return False

        russia_patterns = [
            r"Eneba is not available in Russia",
            r"We support freedom",
            r"not available in Russia",
        ]

        for pattern in russia_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False

    async def _make_request(self, url: str) -> Optional[str]:
        for attempt in range(self.config.retry_attempts):
            try:
                # Случайная задержка
                if attempt > 0:
                    await asyncio.sleep(self.config.retry_delay * attempt)
                else:
                    await asyncio.sleep(
                        random.uniform(self.config.delay_min, self.config.delay_max)
                    )

                # Настройки для curl_cffi
                proxy_config = None
                if self.proxy:
                    proxy_with_country = add_country_to_proxy(self.proxy)
                    proxy_config = {
                        "http": proxy_with_country,
                        "https": proxy_with_country,
                    }
                    country = proxy_with_country.split("country_code=")[1].split(":")[0]
                    # self.logger.debug(f"🇪🇺 Используем страну: {country}")
                async with AsyncSession() as session:
                    response = await session.get(
                        url,
                        # headers=headers,
                        proxies=proxy_config,
                        verify=False,
                        timeout=self.config.timeout,
                    )

                    self.session_stats["total_requests"] += 1

                    if response.status_code == 200:
                        content = response.text
                        if self.is_russia_blocked(content):
                            self.logger.warning(
                                f"🚫 Обнаружена блокировка России для {url}"
                            )
                            self.logger.info(
                                f"🔄 Попытка {attempt + 1}: смена прокси и повтор..."
                            )

                            # Увеличиваем счетчик попыток
                            self.session_stats["retry_attempts"] += 1

                            # Дополнительная задержка
                            await asyncio.sleep(random.uniform(2, 5))

                            # ВАЖНО: continue - переходим к следующей итерации цикла
                            continue

                        # Если блокировки нет - возвращаем контент
                        self.session_stats["successful_requests"] += 1
                        # self.logger.debug(f"✅ Успешно загружен: {url}")
                        return content
                    else:
                        self.logger.warning(f"❌ HTTP {response.status_code} для {url}")
                        if response.status_code in [403, 429]:
                            await asyncio.sleep(random.uniform(5, 10))
                        raise Exception(f"HTTP {response.status_code}")

            except Exception as e:
                self.session_stats["retry_attempts"] += 1
                self.logger.error(
                    f"🔄 Попытка {attempt + 1}/{self.config.retry_attempts} для {url}: {e}"
                )

                if attempt == self.config.retry_attempts - 1:
                    self.session_stats["failed_requests"] += 1
                    self.logger.error(
                        f"❌ Не удалось загрузить {url} после {self.config.retry_attempts} попыток"
                    )

        return None

    async def download_url(self, url: str, filename: Optional[str] = None) -> bool:
        """
        Скачать одну страницу

        Args:
            url: URL для скачивания
            filename: Имя файла для сохранения (если None, генерируется автоматически)

        Returns:
            True если успешно, False если ошибка
        """
        async with self.semaphore:
            try:
                # # Определяем имя файла
                # if filename is None:
                #     filename = self._get_filename_from_url(url)

                # file_path = self.output_path / filename

                # Проверяем, существует ли файл
                if filename.exists():
                    self.logger.info(f"⏭️ Файл {filename} уже существует, пропускаем")
                    return True

                # Скачиваем содержимое
                content = await self._make_request(url)

                if content:
                    # Сохраняем в файл
                    async with aiofiles.open(filename, "w", encoding="utf-8") as f:
                        await f.write(content)

                    self.logger.info(f"💾 Сохранен: {filename}")
                    return True
                else:
                    return False

            except Exception as e:
                self.logger.error(f"❌ Ошибка при скачивании {url}: {e}")
                return False

    async def download_urls(
        self, urls: List, custom_filenames: Optional[Dict[str, str]] = None
    ) -> Dict[str, bool]:
        """Универсальный метод для строк и словарей"""

        self.logger.info(f"🚀 Начинаем загрузку {len(urls)} элементов")

        # Определяем тип данных
        is_products_mode = urls and isinstance(urls[0], dict)
        mode = "продукты" if is_products_mode else "URL"
        self.logger.info(f"📦 Режим: {mode}")

        tasks = []
        for item in urls:
            try:
                if isinstance(item, dict):
                    # РЕЖИМ ПРОДУКТОВ (rozetka)
                    product_slug = item.get("product_slug", "")
                    if not product_slug:
                        continue
                    html_product = get_rozetka_path("html_product")
                    html_file = html_product / f"{product_slug}.html"

                    if html_file.exists():
                        self.logger.debug(f"⏭️ Файл уже существует: {html_file}")
                        continue

                    url = f"https://www.eneba.com/{product_slug}"
                    task = self.download_url(url, html_file)
                    tasks.append((url, task))

                elif isinstance(item, str):
                    # РЕЖИМ URL (pages)
                    url = item
                    filename = custom_filenames.get(url) if custom_filenames else None
                    task = self.download_url(url, filename)
                    tasks.append((url, task))

            except Exception as e:
                self.logger.error(f"❌ Ошибка при обработке {item}: {e}")
                continue
        # Выполняем все задачи
        results = {}
        completed_tasks = await asyncio.gather(
            *[task for _, task in tasks], return_exceptions=True
        )

        for (url, _), result in zip(tasks, completed_tasks):
            if isinstance(result, Exception):
                self.logger.error(f"❌ Исключение для {url}: {result}")
                results[url] = False
            else:
                results[url] = result

        # Выводим статистику
        successful = sum(1 for success in results.values() if success)
        self.logger.info(f"📊 Завершено: {successful}/{len(urls)} успешно")
        self.logger.info(f"📈 Статистика сессии: {self.session_stats}")

        return results

    async def download_from_csv(
        self, csv_file: str, url_column: str = "url"
    ) -> Dict[str, bool]:
        """
        Скачать URL'ы из CSV файла

        Args:
            csv_file: Путь к CSV файлу
            url_column: Название колонки с URL'ами

        Returns:
            Словарь {url: success_status}
        """
        try:
            df = pd.read_csv(csv_file)
            urls = df[url_column].tolist()

            self.logger.info(f"📋 Загружено {len(urls)} URL'ов из {csv_file}")
            return await self.download_urls(urls)

        except Exception as e:
            self.logger.error(f"❌ Ошибка при чтении CSV файла: {e}")
            return {}

    async def _make_post_request(
        self, url: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Выполнить POST запрос с правильными заголовками для Eneba

        Args:
            url: URL для POST запроса
            data: Form data (application/x-www-form-urlencoded)
            json_data: JSON data (application/json)

        Returns:
            Содержимое ответа или None при ошибке
        """
        for attempt in range(self.config.retry_attempts):
            try:
                # Случайная задержка
                if attempt > 0:
                    await asyncio.sleep(self.config.retry_delay * attempt)
                else:
                    await asyncio.sleep(
                        random.uniform(self.config.delay_min, self.config.delay_max)
                    )

                # Настройки для curl_cffi
                proxy_config = None
                if self.proxy:
                    proxy_with_country = add_country_to_proxy(self.proxy)
                    proxy_config = {
                        "http": proxy_with_country,
                        "https": proxy_with_country,
                    }

                async with AsyncSession() as session:
                    # Заголовки специально для Eneba GraphQL API
                    headers = {
                        "accept": "*/*",
                        "accept-language": "en",
                        "cache-control": "no-cache",
                        "content-type": "application/json",
                        "dnt": "1",
                        "origin": "https://www.eneba.com",
                        "pragma": "no-cache",
                        "priority": "u=1, i",
                        "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                        "sec-ch-ua-mobile": "?0",
                        "sec-ch-ua-platform": '"macOS"',
                        "sec-fetch-dest": "empty",
                        "sec-fetch-mode": "cors",
                        "sec-fetch-site": "same-origin",
                        "sec-gpc": "1",
                        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                        "x-version": "1.3109.2",
                    }

                    response = await session.post(
                        url,
                        headers=headers,
                        data=data,
                        json=json_data,
                        proxies=proxy_config,
                        verify=False,
                        timeout=self.config.timeout,
                    )

                    self.session_stats["total_requests"] += 1

                    if response.status_code in [200, 201, 202]:
                        content = response.text
                        self.session_stats["successful_requests"] += 1
                        self.logger.debug(f"✅ POST успешно выполнен: {url}")
                        return content
                    else:
                        self.logger.warning(
                            f"❌ POST HTTP {response.status_code} для {url}"
                        )
                        if response.status_code in [403, 429]:
                            await asyncio.sleep(random.uniform(5, 10))
                        raise Exception(f"HTTP {response.status_code}")

            except Exception as e:
                self.session_stats["retry_attempts"] += 1
                self.logger.error(
                    f"🔄 POST попытка {attempt + 1}/{self.config.retry_attempts} для {url}: {e}"
                )

                if attempt == self.config.retry_attempts - 1:
                    self.session_stats["failed_requests"] += 1
                    self.logger.error(
                        f"❌ Не удалось выполнить POST {url} после {self.config.retry_attempts} попыток"
                    )

        return None

    async def post_url(
        self,
        url: str,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        filename: Optional[str] = None,
    ) -> bool:
        """
        Выполнить POST запрос и сохранить ответ

        Args:
            url: URL для POST запроса
            data: Form data (ключ-значение для form-encoded)
            json_data: JSON data (словарь для JSON)
            filename: Путь к файлу для сохранения (Path объект)

        Returns:
            True если успешно, False если ошибка
        """
        async with self.semaphore:
            try:
                # # Проверяем, существует ли файл
                # if filename and filename.exists():
                #     self.logger.info(f"⏭️ Файл {filename} уже существует, пропускаем")
                #     return True

                # Выполняем POST запрос
                content = await self._make_post_request(url, data, json_data)

                if content:
                    if filename:
                        # Сохраняем в файл
                        async with aiofiles.open(filename, "w", encoding="utf-8") as f:
                            await f.write(content)
                        self.logger.info(f"💾 POST результат сохранен: {filename}")
                    return True
                else:
                    return False

            except Exception as e:
                self.logger.error(f"❌ Ошибка при POST запросе {url}: {e}")
                return False

    async def post_skus(
        self,
        base_url: str,
        skugs: List[Dict],  # Изменено: List[Dict] вместо List[str]
        data_template: Optional[Dict] = None,
        json_template: Optional[Dict] = None,
    ) -> Dict[str, bool]:
        """
        Выполнить POST запросы для списка SKU

        Args:
            base_url: Базовый URL для POST запросов
            skugs: Список словарей SKU для обработки
            data_template: Шаблон form data (SKU будет подставлен в {slug})
            json_template: Шаблон JSON data (SKU будет подставлен в {slug})
            custom_filenames: Словарь {product_slug: filename} для кастомных имен файлов

        Returns:
            Словарь {product_slug: success_status}
        """
        self.logger.info(f"🚀 Начинаем POST запросы для {len(skugs)} SKU")
        self.logger.info(
            f"⚙️ Настройки: {self.config.max_workers} потоков, прокси: {'Да' if self.proxy else 'Нет'}"
        )

        html_product = get_path("html_product")
        json_directory = get_path("json_dir")
        category_id = get_path("category_id")

        # Проверяем валидность путей
        if not (html_product and json_directory):
            self.logger.error("Не удалось получить пути для сохранения файлов")
            return {}

        self.logger.info(f"Файлы HTML будут сохранены в: {html_product}")
        self.logger.info(f"Файлы JSON будут сохранены в: {json_directory}")

        # Рекурсивная функция для замены {slug} во вложенных структурах
        def replace_in_dict(obj, slug_value):
            if isinstance(obj, dict):
                return {k: replace_in_dict(v, slug_value) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_in_dict(item, slug_value) for item in obj]
            elif isinstance(obj, str):
                return obj.format(slug=slug_value)
            else:
                return obj

        # Создаем задачи
        tasks = []

        # УБРАЛ ОГРАНИЧЕНИЕ [:1] - обрабатываем все SKU
        for skug in skugs:
            try:
                # Извлекаем product_slug из словаря
                product_slug = skug.get("product_slug")
                if not product_slug:
                    self.logger.warning(f"⚠️ Отсутствует product_slug в записи: {skug}")
                    continue

                # Подготавливаем данные для каждого SKU
                post_data = None
                post_json = None

                if data_template:
                    post_data = replace_in_dict(data_template, product_slug)

                if json_template:
                    post_json = replace_in_dict(json_template, product_slug)

                # Формируем безопасные имена файлов (заменяем опасные символы)
                safe_slug = (
                    product_slug.replace("-", "_").replace("\\", "_").replace(":", "_")
                )

                # Создаем полные пути к файлам
                filename = json_directory / f"{safe_slug}_price.json"

                # URL может содержать {slug} для подстановки
                if "{slug}" in base_url:
                    url = base_url.format(slug=product_slug)
                else:
                    url = base_url

                # Создаем задачу
                task = self.post_url(url, post_data, post_json, filename)
                tasks.append((product_slug, task))

                self.logger.debug(f"📝 Создана задача для: {product_slug}")

            except Exception as e:
                self.logger.error(f"❌ Ошибка при подготовке задачи для {skug}: {e}")
                continue

        if not tasks:
            self.logger.warning("⚠️ Не создано ни одной задачи для выполнения")
            return {}

        self.logger.info(f"📋 Подготовлено {len(tasks)} задач для выполнения")

        # Выполняем все задачи
        results = {}
        completed_tasks = await asyncio.gather(
            *[task for _, task in tasks], return_exceptions=True
        )

        for (product_slug, _), result in zip(tasks, completed_tasks):
            if isinstance(result, Exception):
                self.logger.error(
                    f"❌ POST исключение для SKU {product_slug}: {result}"
                )
                results[product_slug] = False
            else:
                results[product_slug] = result
                status = "✅ Успешно" if result else "❌ Ошибка"
                self.logger.debug(f"{status}: {product_slug}")

        # Выводим статистику
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful

        self.logger.info(f"📊 POST завершено: {successful}/{len(results)} SKU успешно")
        if failed > 0:
            self.logger.warning(f"❌ Неудачных запросов: {failed}")
        self.logger.info(f"📈 Статистика сессии: {self.session_stats}")

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику сессии"""
        return self.session_stats.copy()

    def reset_stats(self):
        """Сбросить статистику сессии"""
        self.session_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retry_attempts": 0,
        }

    @classmethod
    def create_from_config(
        cls, config_path: Optional[str] = None, proxy_override: Optional[str] = None
    ):
        """
        Удобный метод создания загрузчика из конфига

        Args:
            config_path: Путь к файлу конфигурации (если None, используется стандартный)
            proxy_override: Прокси для переопределения значения из конфига

        Returns:
            Экземпляр Downloader
        """
        config = Config.load()
        return cls(config, proxy_override)


config = Config.load()
downloader = Downloader(config)


# Универсальные функции для быстрого использования
async def download_urls_simple(
    urls: List[str], max_workers: int = 10, proxy: Optional[str] = None
) -> Dict[str, bool]:
    """
    Простая функция для скачивания URL'ов без лишних настроек

    Args:
        urls: Список URL'ов
        max_workers: Количество потоков
        proxy: Прокси (опционально)

    Returns:
        Результаты скачивания
    """
    config = Config.load()
    # Переопределяем max_workers если передан
    config.client.max_workers = max_workers

    downloader = Downloader(config, proxy)
    return await downloader.download_urls(urls)


async def download_from_csv_simple(
    csv_file: str, max_workers: int = 10, proxy: Optional[str] = None
) -> Dict[str, bool]:
    """
    Простая функция для скачивания из CSV файла

    Args:
        csv_file: Путь к CSV файлу
        max_workers: Количество потоков
        proxy: Прокси (опционально)

    Returns:
        Результаты скачивания
    """
    config = Config.load()
    config.client.max_workers = max_workers

    downloader = Downloader(config, proxy)
    return await downloader.download_from_csv(csv_file)


# # Пример использования
# async def main():
#     """Пример использования класса Downloader с вашим конфигом"""

#     # Список URL'ов для скачивания
#     start_xml_path = paths.data / "sitemap.xml"
#     output_csv_file = paths.data / "output.csv"
#     df = pd.read_csv(output_csv_file, encoding="utf-8")
#     urls = df["url"].tolist()
#     # Скачиваем
#     results = await downloader.download_urls(urls)

#     # Результаты
#     logger.info("🎯 Результаты:")
#     for url, success in results.items():
#         status = "✅ Успешно" if success else "❌ Ошибка"
#         logger.info(f"{status}: {url}")

#     # Статистика
#     logger.info(f"\n📊 Финальная статистика: {downloader.get_stats()}")


# if __name__ == "__main__":
#     asyncio.run(main())
