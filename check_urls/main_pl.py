import asyncio
import json
import os
import time
from urllib.parse import urlparse

import pandas as pd
from playwright.async_api import async_playwright


async def check_url_with_playwright(main_url, additional_url, timeout=30000):
    """
    Проверяет URL с помощью Playwright для имитации реального браузера.

    Args:
        main_url: Основной URL (из первой колонки)
        additional_url: Дополнительный URL для проверки (из второй колонки)
        timeout: Таймаут в миллисекундах (30 секунд по умолчанию)

    Returns:
        Словарь с результатами проверки
    """
    result = {
        "основной_url": main_url,
        "дополнительный_url": additional_url,
        "финальный_url": "",
        "код_статуса": None,
        "работает": False,
        "причина": "",
        "есть_контент": False,
        "маршрут_редиректов": [],
        "время_загрузки_мс": None,
        "скриншот_путь": None,
    }

    async with async_playwright() as playwright:
        browser = None
        try:
            # Запускаем браузер
            browser = await playwright.chromium.launch(
                headless=True
            )  # headless=True для работы без UI
            context = await browser.new_context(
                bypass_csp=True,
                java_script_enabled=True,
                permissions=["geolocation"],
                device_scale_factor=1.0,
                has_touch=True,
                ignore_https_errors=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            )

            # Создаем страницу и настраиваем обработчики событий
            page = await context.new_page()

            # Отслеживание редиректов и статус-кодов
            redirects = []

            # Обработчик для перехвата ответов сети
            async def handle_response(response):
                redirects.append(
                    {
                        "url": response.url,
                        "status": response.status,
                        "headers": dict(response.headers),
                    }
                )

                # Сохраняем код статуса последнего ответа
                result["код_статуса"] = response.status

            # Подписываемся на события ответов
            page.on("response", handle_response)

            # Засекаем время начала загрузки
            start_time = time.time()

            # Переходим на URL с таймаутом
            try:
                # Переходим на URL и ждем загрузки страницы
                await page.goto(
                    additional_url, timeout=timeout, wait_until="networkidle"
                )

                # Считаем время загрузки
                result["время_загрузки_мс"] = int((time.time() - start_time) * 1000)

                # Получаем финальный URL
                result["финальный_url"] = page.url

                # Проверка наличия контента
                content_check = await page.evaluate(
                    """
                    () => {
                        const bodyContent = document.body.innerText.trim();
                        return {
                            hasBody: document.body !== null,
                            hasContent: bodyContent.length > 50,
                            childElements: document.body ? document.body.children.length : 0
                        };
                    }
                """
                )

                result["есть_контент"] = (
                    content_check["hasContent"] and content_check["childElements"] > 0
                )

                # Проверяем соответствие доменов
                main_domain = urlparse(main_url).netloc.replace("www.", "")
                final_domain = urlparse(page.url).netloc.replace("www.", "")
                domains_match = main_domain == final_domain

                # Делаем скриншот
                screenshots_dir = "screenshots"
                os.makedirs(screenshots_dir, exist_ok=True)
                screenshot_path = f"{screenshots_dir}/{urlparse(additional_url).netloc.replace('.', '_')}.png"
                await page.screenshot(path=screenshot_path)
                result["скриншот_путь"] = screenshot_path

                # Формируем маршрут редиректов
                result["маршрут_редиректов"] = [r["url"] for r in redirects]

                # Определяем работоспособность
                if 200 <= result["код_статуса"] < 400:
                    result["работает"] = True
                    if not domains_match:
                        result["работает"] = False
                        result["причина"] = (
                            f"Домен финального URL не совпадает с основным ({final_domain} vs {main_domain})"
                        )
                elif 400 <= result["код_статуса"] < 500:
                    if result["есть_контент"] and domains_match:
                        result["работает"] = True
                        result["причина"] = (
                            f"HTTP ошибка {result['код_статуса']}, но страница загрузилась (домены совпадают)"
                        )
                    else:
                        result["причина"] = f"HTTP ошибка {result['код_статуса']}"
                elif 500 <= result["код_статуса"] < 600:
                    result["причина"] = f"Серверная ошибка {result['код_статуса']}"
                else:
                    result["причина"] = f"Нестандартный код {result['код_статуса']}"

            except Exception as navigation_error:
                error_message = str(navigation_error)

                # Проверяем, завершилась ли навигация с ошибкой таймаута
                if "Timeout" in error_message:
                    result["причина"] = f"Таймаут при загрузке страницы ({timeout}мс)"
                elif "ERR_NAME_NOT_RESOLVED" in error_message:
                    result["причина"] = "Не удалось разрешить доменное имя"
                elif "ERR_CONNECTION_REFUSED" in error_message:
                    result["причина"] = "Соединение отклонено"
                elif "ERR_SSL" in error_message:
                    result["причина"] = "Ошибка SSL-сертификата"
                else:
                    result["причина"] = f"Ошибка навигации: {error_message}"

                # Даже при ошибке, возможно, был частичный успех с редиректами
                if redirects:
                    result["маршрут_редиректов"] = [r["url"] for r in redirects]
                    result["финальный_url"] = redirects[-1]["url"]
                    result["код_статуса"] = redirects[-1]["status"]

        except Exception as e:
            result["причина"] = f"Неожиданная ошибка: {str(e)}"

        finally:
            # Закрываем браузер
            if browser:
                await browser.close()

    return result


async def process_urls(url_list):
    """
    Обрабатывает список URL асинхронно.
    """
    results = []

    for main_url, additional_url in url_list:
        main_url = main_url.strip() if main_url else additional_url
        additional_url = additional_url.strip()

        if not additional_url:
            additional_url = main_url

        print(f"Проверка: {additional_url}")
        result = await check_url_with_playwright(main_url, additional_url)
        results.append(result)

        # Небольшая пауза между запросами
        await asyncio.sleep(1)

    return results


def save_results(
    results,
    output_file="результаты_проверки_url.csv",
    full_output_file="полные_результаты_проверки.json",
):
    """
    Сохраняет результаты в CSV и JSON форматы.
    """
    # Создаем DataFrame для CSV
    df_data = []
    for result in results:
        # Извлекаем только базовые поля для CSV
        row = {
            "Основной URL": result["основной_url"],
            "Начальный URL": result["дополнительный_url"],
            "Финальный URL": result["финальный_url"],
            "Код статуса": result["код_статуса"],
            "Работает": result["работает"],
            "Причина": result["причина"],
            "Есть контент": result["есть_контент"],
            "Время загрузки (мс)": result["время_загрузки_мс"],
            "Скриншот": result["скриншот_путь"],
        }
        df_data.append(row)

    df = pd.DataFrame(df_data)
    df.to_csv(output_file, index=False)

    # Сохраняем полные результаты в JSON
    with open(full_output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return df


def load_urls_from_csv(file_path):
    """
    Загружает URL из CSV-файла.
    """
    # Пробуем разные разделители
    try:
        df = pd.read_csv(file_path, sep=";")
    except:
        try:
            df = pd.read_csv(file_path, sep=",")
        except:
            try:
                # В случае ошибки пробуем определить разделитель автоматически
                with open(file_path, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()

                if "," in first_line:
                    df = pd.read_csv(file_path, sep=",")
                elif ";" in first_line:
                    df = pd.read_csv(file_path, sep=";")
                elif "\t" in first_line:
                    df = pd.read_csv(file_path, sep="\t")
                else:
                    raise ValueError("Не удалось определить разделитель в CSV-файле")
            except Exception as e:
                raise ValueError(f"Ошибка при чтении CSV-файла: {str(e)}")

    # Проверяем наличие нужных колонок
    if "URL" in df.columns and "ClickUrl" in df.columns:
        test_urls = list(zip(df["URL"], df["ClickUrl"]))
    else:
        # Пробуем найти колонки по альтернативным названиям
        url_columns = [
            col for col in df.columns if "url" in col.lower() or "ссылк" in col.lower()
        ]

        if len(url_columns) >= 2:
            test_urls = list(zip(df[url_columns[0]], df[url_columns[1]]))
        elif len(url_columns) == 1:
            # Если только одна колонка с URL, используем ее дважды
            test_urls = list(zip(df[url_columns[0]], df[url_columns[0]]))
        else:
            # Берем первые две колонки
            test_urls = list(
                zip(df.iloc[:, 0], df.iloc[:, 1] if df.shape[1] > 1 else df.iloc[:, 0])
            )

    return test_urls


async def main():
    import sys

    # Проверяем наличие аргумента с путем к CSV-файлу
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = "shop_export for test.csv"

    try:
        # Загружаем URLs из CSV
        test_urls = load_urls_from_csv(csv_file)
        print(f"Загружено {len(test_urls)} URL из файла {csv_file}")

        # Обрабатываем URLs
        results = await process_urls(test_urls)

        # Сохраняем результаты
        df = save_results(results)
        print("\nРезультаты (основные):")
        print(df.head().to_string())

        print(f"\nВсего проверено URL: {len(results)}")
        print(f"Работающих URL: {sum(r['работает'] for r in results)}")
        print(f"Неработающих URL: {sum(not r['работает'] for r in results)}")

        print("\nПолные результаты сохранены в файл 'полные_результаты_проверки.json'")
        print("Скриншоты сохранены в папку 'screenshots'")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")


# Запускаем асинхронную функцию main()
if __name__ == "__main__":
    asyncio.run(main())
