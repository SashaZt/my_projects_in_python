import json
import os
import time

import requests
from kostrost.all_site.config.logger import logger


class ScraperAPIAsync:
    def __init__(self, api_key, max_retries=3, delay_between_requests=1):
        self.api_key = api_key
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        # Асинхронный API ScraperAPI
        self.base_url = "https://async.scraperapi.com/jobs"

    def download_batch(self, urls_batch, output_dirs):
        """
        Downloads multiple URLs in a batch using the async API

        Args:
            urls_batch: List of URLs to download
            output_dirs: Dictionary mapping URLs to their output directories

        Returns:
            Dictionary mapping URLs to success status (True/False)
        """
        if not urls_batch:
            return {}

        logger.info(f"Sending batch request for {len(urls_batch)} URLs")

        # Создаем задание на скачивание
        job_id = self._create_batch_job(urls_batch)
        if not job_id:
            logger.error("Failed to create batch job")
            return {url: False for url in urls_batch}

        # Ожидаем выполнения задания
        results = self._poll_batch_job(job_id)
        if not results:
            logger.error("No results received from batch job")
            return {url: False for url in urls_batch}

        # Обрабатываем результаты
        return self._process_batch_results(results, output_dirs)

    def _create_batch_job(self, urls):
        """Creates a batch job and returns the job ID"""
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url=self.base_url,
                    json={
                        "apiKey": self.api_key,
                        "urls": urls,
                        "country_code": "pl",  # Опционально: страна прокси
                        "render": True,  # Опционально: JavaScript рендеринг
                    },
                    timeout=60,
                )

                if response.status_code == 200:
                    job_data = response.json()
                    job_id = job_data.get("id")

                    if job_id:
                        logger.info(f"Created batch job {job_id} for {len(urls)} URLs")
                        return job_id
                    else:
                        logger.error(f"No job ID in response: {job_data}")
                else:
                    logger.error(
                        f"Error creating batch job: {response.status_code} - {response.text}"
                    )

            except Exception as e:
                logger.error(f"Exception creating batch job: {str(e)}")

            # Увеличиваем задержку с каждой попыткой
            retry_delay = self.delay_between_requests * (attempt + 1)
            logger.warning(
                f"Attempt {attempt+1} failed. Retrying in {retry_delay} seconds..."
            )
            time.sleep(retry_delay)

        return None

    def _poll_batch_job(self, job_id, max_polls=30, poll_interval=5):
        """Polls for batch job completion and returns results"""
        for poll_num in range(max_polls):
            try:
                time.sleep(poll_interval)

                status_response = requests.get(
                    f"{self.base_url}/{job_id}",
                    params={"apiKey": self.api_key},
                    timeout=30,
                )

                if status_response.status_code != 200:
                    logger.error(
                        f"Error checking batch status: {status_response.status_code}"
                    )
                    continue

                status_data = status_response.json()
                status = status_data.get("status")

                logger.info(
                    f"Batch job {job_id} status: {status} (Poll {poll_num+1}/{max_polls})"
                )

                if status == "finished":
                    # Когда задание завершено, запрашиваем результаты
                    result_response = requests.get(
                        f"{self.base_url}/{job_id}/result",
                        params={"apiKey": self.api_key},
                        timeout=60,
                    )

                    if result_response.status_code == 200:
                        return result_response.json()
                    else:
                        logger.error(
                            f"Error getting batch results: {result_response.status_code}"
                        )
                        return None

                elif status == "failed":
                    error = status_data.get("error") or "Unknown error"
                    logger.error(f"Batch job failed: {error}")
                    return None

                # Задание всё ещё выполняется, продолжаем опрос
                logger.info(
                    f"Batch job in progress, waiting {poll_interval} seconds..."
                )

            except Exception as e:
                logger.error(f"Error polling batch status: {str(e)}")

        logger.error(f"Polling timed out for batch job {job_id}")
        return None

    def _process_batch_results(self, results, output_dirs):
        """
        Processes batch results and saves HTML files

        Args:
            results: Results from the batch job
            output_dirs: Dictionary mapping URLs to output directories

        Returns:
            Dictionary mapping URLs to success status (True/False)
        """
        success_map = {}

        try:
            # Проверяем формат результатов
            if not isinstance(results, list):
                logger.error(f"Unexpected results format: {type(results)}")
                return {url: False for url in output_dirs.keys()}

            # Обрабатываем каждый результат
            for result in results:
                url = result.get("url")
                status_code = result.get("statusCode")
                html_content = result.get("response", {}).get("body")

                if not url or url not in output_dirs:
                    logger.warning(f"Unknown URL in results: {url}")
                    continue

                output_dir = output_dirs[url]

                if status_code == 200 and html_content:
                    # Создаем имя файла на основе URL
                    filename = url.split("/")[-1]
                    if not filename:
                        filename = "index"
                    filename = f"{filename}.html"

                    # Полный путь к файлу
                    file_path = os.path.join(output_dir, filename)

                    # Сохраняем HTML-контент
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(html_content)

                    logger.info(f"Successfully saved {url} to {file_path}")
                    success_map[url] = True
                else:
                    error_msg = result.get("error") or f"Status code: {status_code}"
                    logger.error(f"Failed to download {url}: {error_msg}")
                    success_map[url] = False

        except Exception as e:
            logger.error(f"Error processing batch results: {str(e)}")
            # В случае ошибки считаем, что все URL не удалось скачать
            return {url: False for url in output_dirs.keys()}

        return success_map


# Пример использования
if __name__ == "__main__":
    api_key = "d415ddc01cf23948eff76e4447f69372"
    scraper = ScraperAPIAsync(api_key)

    # Тестовые URL и директории
    urls = [
        "https://guitarcenter.pl/catalog/gitary/gitary/gitary-akustyczne/alvarez-ad-30",
        "https://thomann.de/gb/harley_benton_dc_junior_ltd_black.htm",
    ]

    # Создаем тестовые директории
    test_dirs = {}
    for i, url in enumerate(urls):
        dir_name = f"test_dir_{i+1}"
        os.makedirs(dir_name, exist_ok=True)
        test_dirs[url] = dir_name

    # Скачиваем пакетом
    results = scraper.download_batch(urls, test_dirs)

    # Выводим результаты
    for url, success in results.items():
        status = "Success" if success else "Failed"
        print(f"{status}: {url}")
