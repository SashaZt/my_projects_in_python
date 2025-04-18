import base64
import time
from pathlib import Path

import requests
import settings
from config.logger import logger


class BaseScraper:
    """Базовый класс для скрапера"""

    def __init__(self, api_key=None):
        """
        Инициализация базового скрапера

        Args:
            api_key: API ключ для ScraperAPI
        """
        self.api_key = api_key or settings.API_KEY

    def check_job_status(self, job_info):
        """
        Проверяет статус существующего задания

        Args:
            job_info: Информация о задании

        Returns:
            Tuple (status_code, html_content):
                - status_code: 'finished', 'running', 'failed' или None
                - html_content: HTML-контент (если задание завершено) или None
        """
        job_id = job_info.get("id")
        if not job_id:
            return None, None

        url = job_info.get("url")
        status_url = f"https://async.scraperapi.com/jobs/{job_id}"

        logger.info(f"Проверка статуса задания {job_id} для URL {url}")

        try:
            # Проверяем статус задания
            status_response = requests.get(
                status_url,
                params={"apiKey": self.api_key},
                timeout=settings.REQUEST_TIMEOUT,
            )

            if status_response.status_code != 200:
                logger.error(
                    f"Ошибка при проверке статуса: {status_response.status_code}"
                )
                return "error", None

            status_data = status_response.json()
            job_status = status_data.get("status")

            logger.info(f"Статус задания {job_id}: {job_status}")

            if job_status == "finished":
                # Получаем результат
                result_url = f"{status_url}/result"
                result_response = requests.get(
                    result_url,
                    params={"apiKey": self.api_key},
                    timeout=settings.RESULT_TIMEOUT,
                )

                if result_response.status_code == 200:
                    result_data = result_response.json()

                    # Получаем HTML-контент
                    html_content = None

                    # Проверяем структуру ответа
                    if isinstance(result_data, list):
                        # Если результат - список (для batch-запросов)
                        for item in result_data:
                            if item.get("url") == url:
                                html_content = item.get("response", {}).get("body")
                                break
                    else:
                        # Проверяем наличие response и body в ответе
                        if (
                            "response" in result_data
                            and "body" in result_data["response"]
                        ):
                            html_content = result_data["response"]["body"]
                        # Иногда тело может быть закодировано в base64
                        elif (
                            "response" in result_data
                            and "base64EncodedBody" in result_data["response"]
                        ):
                            encoded_body = result_data["response"]["base64EncodedBody"]
                            html_content = base64.b64decode(encoded_body).decode(
                                "utf-8", errors="replace"
                            )

                    if html_content:
                        return "finished", html_content
                    else:
                        logger.error(f"HTML-контент не найден для URL {url}")
                        logger.debug(f"Структура ответа: {result_data}")
                        return "failed", None

                elif result_response.status_code == 404:
                    # Если задание завершено, но результат не найден, пробуем получить HTML из статуса
                    logger.warning(
                        f"Результат задания {job_id} не найден (404), пробуем извлечь из статуса"
                    )

                    # Проверяем, есть ли response в данных статуса
                    if "response" in status_data:
                        if "body" in status_data["response"]:
                            html_content = status_data["response"]["body"]
                            return "finished", html_content
                        elif "base64EncodedBody" in status_data["response"]:
                            encoded_body = status_data["response"]["base64EncodedBody"]
                            html_content = base64.b64decode(encoded_body).decode(
                                "utf-8", errors="replace"
                            )
                            return "finished", html_content

                    logger.error(f"Не удалось извлечь HTML из статуса задания {job_id}")
                    return "failed", None
                else:
                    logger.error(
                        f"Ошибка при получении результата: {result_response.status_code}"
                    )
                    return "failed", None

            elif job_status == "failed":
                error = status_data.get("error") or "Неизвестная ошибка"
                logger.error(f"Задание для URL {url} не выполнено: {error}")
                return "failed", None

            elif job_status == "running":
                # Задание все еще выполняется
                logger.info(f"Задание {job_id} все еще выполняется.")
                return "running", None

            else:
                logger.warning(f"Неизвестный статус задания {job_id}: {job_status}")
                return "unknown", None

        except Exception as e:
            logger.error(f"Ошибка при проверке статуса задания {job_id}: {str(e)}")
            return "error", None

    def submit_job(self, url):
        """
        Отправляет задание на скрапинг для указанного URL

        Args:
            url: URL страницы

        Returns:
            dict: информация о задании или None в случае ошибки
        """
        max_retries = settings.MAX_SUBMIT_RETRIES

        for attempt in range(max_retries):
            try:
                # Используем асинхронный API
                response = requests.post(
                    url="https://async.scraperapi.com/jobs",
                    json={
                        "apiKey": self.api_key,
                        "url": url,
                    },
                    timeout=settings.REQUEST_TIMEOUT,
                )

                if response.status_code == 200:
                    response_data = response.json()
                    job_id = response_data.get("id")

                    # Формируем информацию о задании
                    job_info = {
                        "id": job_id,
                        "url": url,
                        "status": "submitted",
                        "submitted_at": time.time(),
                    }

                    logger.info(
                        f"Асинхронное задание {job_id} отправлено для URL {url}"
                    )
                    return job_info
                else:
                    logger.error(
                        f"Ошибка при отправке задания для URL {url}: {response.status_code} - {response.text}"
                    )
                    time.sleep((attempt + 1) * 2)

            except Exception as e:
                logger.error(f"Ошибка при отправке задания для URL {url}: {str(e)}")
                time.sleep((attempt + 1) * 2)

        logger.error(
            f"Не удалось отправить задание для URL {url} после {max_retries} попыток"
        )
        return None
