import time
from urllib.parse import urlparse

import pandas as pd
import requests
from requests.exceptions import RequestException


def check_url(main_url, additional_url, timeout=10, max_redirects=10):
    result = {
        "основной_url": main_url,
        "дополнительный_url": additional_url,
        "финальный_url": "",
        "код_статуса": None,
        "работает": False,
        "причина": "",
        "есть_контент": False,
    }

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        }

        session = requests.Session()
        session.max_redirects = max_redirects

        response = session.get(
            additional_url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
        )

        result["код_статуса"] = response.status_code
        result["финальный_url"] = response.url

        if "<html" in response.text.lower() and "<app-root" in response.text.lower():
            result["есть_контент"] = True

        main_domain = urlparse(main_url).netloc
        final_domain = urlparse(response.url).netloc
        domains_match = main_domain == final_domain

        if 200 <= response.status_code < 400:
            result["работает"] = True
            if not domains_match:
                result["работает"] = False
                result["причина"] = "Домен финального URL не совпадает с основным URL"
        elif result["код_статуса"] == 404 and result["есть_контент"] and domains_match:
            result["работает"] = True
            result["причина"] = (
                "HTTP Ошибка 404, но страница загрузилась (домены совпадают)"
            )
        else:
            result["причина"] = f"HTTP Ошибка {response.status_code}"

    except requests.exceptions.Timeout:
        result["причина"] = "Тайм-аут соединения"
    except requests.exceptions.TooManyRedirects:
        result["причина"] = "Слишком много перенаправлений"
    except requests.exceptions.SSLError:
        result["причина"] = "Ошибка SSL-сертификата"
    except requests.exceptions.ConnectionError:
        result["причина"] = "Ошибка соединения"
    except RequestException as e:
        result["причина"] = f"Ошибка запроса: {str(e)}"

    return result


def process_urls(url_list):
    results = []

    for main_url, additional_url in url_list:
        main_url = main_url.strip() if main_url else additional_url
        additional_url = additional_url.strip()

        if not additional_url:
            additional_url = main_url

        print(f"Проверка: {additional_url}")
        result = check_url(main_url, additional_url)
        results.append(result)
        time.sleep(1)  # Задержка между запросами

    return results


def save_results(results, output_file="результаты_проверки_url.csv"):
    df = pd.DataFrame(results)
    df.columns = [
        "Основной URL",
        "Начальный URL",
        "Финальный URL",
        "Код статуса",
        "Работает",
        "Причина",
        "Есть контент",
    ]
    df.to_csv(output_file, index=False)
    return df


# Зчитування CSV-файлу
def load_urls_from_csv(file_path):
    # Читаємо CSV із роздільником ";"
    df = pd.read_csv(file_path, sep=";")
    # Перетворюємо в список кортежів (URL, ClickUrl)
    test_urls = list(zip(df["URL"], df["ClickUrl"]))
    return test_urls


if __name__ == "__main__":
    # Шлях до вашого CSV-файлу
    csv_file = "shop_export for test.csv"

    # Завантажуємо URL із CSV
    test_urls = load_urls_from_csv(csv_file)

    # Обробляємо URL
    results = process_urls(test_urls)

    # Зберігаємо та виводимо результати
    df = save_results(results)
    print("\nРезультаты:")
    print(df.to_string())
