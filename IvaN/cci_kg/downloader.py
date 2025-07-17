import asyncio
import hashlib
import random
from typing import Any, Dict, List, Optional

import aiofiles
import pandas as pd
from curl_cffi.requests import AsyncSession

from config import Config, logger, paths

cookies = {
    "PHPSESSID": "n2uiuqm8e2u1ose7iend6r11l1",
    "astratop": "1",
}


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
        self.output_path = paths.html

        # Используем глобальный логгер
        self.logger = logger

    # def _get_random_user_agent(self) -> str:
    #     """Получить случайный User-Agent из конфига"""
    #     return random.choice(self.config.user_agents)

    def _get_filename_from_url(self, url: str) -> str:
        """Генерировать имя файла на основе URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return f"{url_hash}.html"

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
                    proxy_config = {"http": self.proxy, "https": self.proxy}
                async with AsyncSession() as session:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "Cache-Control": "max-age=0",
                    }

                    response = await session.get(
                        url,
                        cookies=cookies,
                        headers=headers,
                        proxies=proxy_config,
                        verify=False,
                        timeout=self.config.timeout,
                    )

                    self.session_stats["total_requests"] += 1

                    if response.status_code == 200:
                        content = response.text
                        self.session_stats["successful_requests"] += 1
                        self.logger.debug(f"✅ Успешно загружен: {url}")
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
                # Определяем имя файла
                if filename is None:
                    filename = self._get_filename_from_url(url)

                file_path = self.output_path / filename

                # Проверяем, существует ли файл
                if file_path.exists():
                    self.logger.info(f"⏭️ Файл {file_path} уже существует, пропускаем")
                    return True

                # Скачиваем содержимое
                content = await self._make_request(url)

                if content:
                    # Сохраняем в файл
                    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                        await f.write(content)

                    self.logger.info(f"💾 Сохранен: {file_path}")
                    return True
                else:
                    return False

            except Exception as e:
                self.logger.error(f"❌ Ошибка при скачивании {url}: {e}")
                return False

    async def download_urls(
        self, urls: List[str], custom_filenames: Optional[Dict[str, str]] = None
    ) -> Dict[str, bool]:
        """
        Скачать множество URL'ов

        Args:
            urls: Список URL'ов для скачивания
            custom_filenames: Словарь {url: filename} для кастомных имен файлов

        Returns:
            Словарь {url: success_status}
        """
        self.logger.info(f"🚀 Начинаем загрузку {len(urls)} URL'ов")
        self.logger.info(
            f"⚙️ Настройки: {self.config.max_workers} потоков, прокси: {'Да' if self.proxy else 'Нет'}"
        )

        # Создаем задачи
        tasks = []
        for url in urls:
            filename = custom_filenames.get(url) if custom_filenames else None
            task = self.download_url(url, filename)
            tasks.append((url, task))

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
        Выполнить POST запрос

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
                    proxy_config = {"http": self.proxy, "https": self.proxy}

                async with AsyncSession() as session:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "Cache-Control": "max-age=0",
                    }

                    # Определяем тип контента
                    if json_data:
                        headers["Content-Type"] = "application/json"
                    elif data:
                        headers["Content-Type"] = "application/x-www-form-urlencoded"

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
            filename: Имя файла для сохранения (если None, генерируется автоматически)

        Returns:
            True если успешно, False если ошибка
        """
        async with self.semaphore:
            try:
                # Определяем имя файла если не передано
                if filename is None:
                    filename = self._get_filename_from_url(f"{url}_post")

                # Проверяем, существует ли файл
                if Path(filename).exists():
                    self.logger.info(f"⏭️ Файл {filename} уже существует, пропускаем")
                    return True

                # Выполняем POST запрос
                content = await self._make_post_request(url, data, json_data)

                if content:
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

    async def post_urls(self, requests_data: List[Dict]) -> Dict[str, bool]:
        """
        Выполнить множество POST запросов

        Args:
            requests_data: Список словарей с данными для запросов
                        Каждый словарь должен содержать:
                        - 'url': обязательно
                        - 'data': опционально (form data)
                        - 'json_data': опционально (json data)
                        - 'filename': опционально (имя файла)

        Returns:
            Словарь {url: success_status}
        """
        self.logger.info(f"🚀 Начинаем выполнение {len(requests_data)} POST запросов")
        self.logger.info(
            f"⚙️ Настройки: {self.config.max_workers} потоков, прокси: {'Да' if self.proxy else 'Нет'}"
        )

        # Создаем задачи
        tasks = []
        for request_info in requests_data:
            url = request_info["url"]
            data = request_info.get("data")
            json_data = request_info.get("json_data")
            filename = request_info.get("filename")

            task = self.post_url(url, data, json_data, filename)
            tasks.append((url, task))

        # Выполняем все задачи
        results = {}
        completed_tasks = await asyncio.gather(
            *[task for _, task in tasks], return_exceptions=True
        )

        for (url, _), result in zip(tasks, completed_tasks):
            if isinstance(result, Exception):
                self.logger.error(f"❌ POST исключение для {url}: {result}")
                results[url] = False
            else:
                results[url] = result

        # Выводим статистику
        successful = sum(1 for success in results.values() if success)
        self.logger.info(
            f"📊 POST завершено: {successful}/{len(requests_data)} успешно"
        )
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


# Пример использования
async def main():
    """Пример использования класса Downloader с вашим конфигом"""

    # Список URL'ов для скачивания
    start_xml_path = paths.data / "sitemap.xml"
    output_csv_file = paths.data / "output.csv"
    df = pd.read_csv(output_csv_file, encoding="utf-8")
    urls = df["url"].tolist()
    # Скачиваем
    results = await downloader.download_urls(urls)

    # Результаты
    logger.info("🎯 Результаты:")
    for url, success in results.items():
        status = "✅ Успешно" if success else "❌ Ошибка"
        logger.info(f"{status}: {url}")

    # Статистика
    logger.info(f"\n📊 Финальная статистика: {downloader.get_stats()}")


if __name__ == "__main__":
    asyncio.run(main())
