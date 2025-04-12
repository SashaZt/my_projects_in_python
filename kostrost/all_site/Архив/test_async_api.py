import json
import os
import time

import requests
from kostrost.all_site.config.logger import logger


def test_async_api():
    """Тестирует асинхронный API ScraperAPI с базовыми URL и проверяет результаты"""

    API_KEY = "d415ddc01cf23948eff76e4447f69372"
    BASE_URL = "https://async.scraperapi.com/jobs"

    # Тестовые URL-адреса
    test_urls = [
        "https://guitarcenter.pl/catalog/gitary/gitary/gitary-akustyczne/alvarez-ad-30",
        "https://www.thomann.de/gb/index.html",
    ]

    logger.info("Тестирование асинхронного API ScraperAPI")

    # Шаг 1: Создание задания
    try:
        logger.info(f"Создание задания для {len(test_urls)} URL")

        for url in test_urls:
            logger.info(f"Тестовый URL: {url}")

            response = requests.post(
                url=BASE_URL, json={"apiKey": API_KEY, "urls": url}, timeout=30
            )

            if response.status_code != 200:
                logger.error(
                    f"Ошибка при создании задания: {response.status_code} - {response.text}"
                )
                return False

            job_data = response.json()
            job_id = job_data.get("id")

            if not job_id:
                logger.error(f"Не получен ID задания: {job_data}")
                return False

            logger.info(f"Создано задание с ID: {job_id}")

        # Шаг 2: Опрос статуса задания
        max_polls = 20
        poll_interval = 5

        for poll_num in range(max_polls):
            logger.info(f"Опрос статуса задания {poll_num+1}/{max_polls}")

            time.sleep(poll_interval)

            status_response = requests.get(
                f"{BASE_URL}/{job_id}", params={"apiKey": API_KEY}, timeout=30
            )

            if status_response.status_code != 200:
                logger.error(
                    f"Ошибка при опросе статуса: {status_response.status_code}"
                )
                continue

            status_data = status_response.json()
            status = status_data.get("status")

            logger.info(f"Статус задания: {status}")

            if status == "finished":
                # Шаг 3: Получение результатов
                result_response = requests.get(
                    f"{BASE_URL}/{job_id}/result",
                    params={"apiKey": API_KEY},
                    timeout=60,
                )

                if result_response.status_code != 200:
                    logger.error(
                        f"Ошибка при получении результатов: {result_response.status_code}"
                    )
                    return False

                # Сохраняем результаты в файл для анализа
                results = result_response.json()

                with open("test_async_results.json", "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=4, ensure_ascii=False)

                logger.info(f"Результаты сохранены в test_async_results.json")

                # Сохраняем HTML-контент для каждого URL
                if isinstance(results, list):
                    for i, result in enumerate(results):
                        url = result.get("url")
                        html_content = result.get("response", {}).get("body")

                        if html_content:
                            filename = f"test_async_{i+1}.html"
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write(html_content)
                            logger.info(f"HTML для {url} сохранен в {filename}")

                return True

            elif status == "failed":
                error = status_data.get("error") or "Неизвестная ошибка"
                logger.error(f"Задание не выполнено: {error}")
                return False

        logger.error(f"Превышено время ожидания для задания {job_id}")
        return False

    except Exception as e:
        logger.error(f"Ошибка при тестировании API: {str(e)}")
        return False


if __name__ == "__main__":
    if test_async_api():
        logger.info("Тест асинхронного API успешно завершен")
    else:
        logger.error("Тест асинхронного API завершился с ошибкой")
