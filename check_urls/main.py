import json
import random
import time
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from requests.exceptions import RequestException


def manually_follow_redirects(url, max_redirects=10, timeout=10):
    redirects = []
    current_url = url
    status_code = None
    final_content = None
    redirect_count = 0
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Referer": "https://google.com",
    }

    session = requests.Session()

    while redirect_count < max_redirects:
        try:
            response = session.get(
                current_url, headers=headers, timeout=timeout, allow_redirects=False
            )
            status_code = response.status_code

            redirect_info = {
                "url": current_url,
                "status_code": status_code,
                "is_redirect": 300 <= status_code < 400,
                "redirect_location": response.headers.get("Location", ""),
                "content_type": response.headers.get("Content-Type", ""),
            }
            redirects.append(redirect_info)

            if 300 <= status_code < 400:
                redirect_location = redirect_info["redirect_location"]
                if not redirect_location:
                    break
                next_url = urljoin(current_url, redirect_location)
                if next_url in [r["url"] for r in redirects]:
                    break
                current_url = next_url
                redirect_count += 1
            else:
                final_content = response.text
                break

        except Exception as e:
            redirect_info = {
                "url": current_url,
                "status_code": None,
                "is_redirect": False,
                "error": str(e),
            }
            redirects.append(redirect_info)
            break

    # Додатковий простий запит із автоматичними редиректами
    if status_code == 403:
        try:
            simple_response = session.get(
                url, headers=headers, timeout=timeout, allow_redirects=True
            )
            status_code = simple_response.status_code
            final_content = simple_response.text
            redirects.append(
                {
                    "url": simple_response.url,
                    "status_code": status_code,
                    "is_redirect": False,
                    "content_type": simple_response.headers.get("Content-Type", ""),
                }
            )
            current_url = simple_response.url
        except Exception as e:
            redirects[-1]["error"] = str(e)

    result = {
        "redirects": redirects,
        "final_url": current_url,
        "final_status_code": status_code,
        "redirect_count": redirect_count,
        "max_redirects_reached": redirect_count >= max_redirects,
        "content": final_content[:10000] if final_content else None,
    }
    return result


def check_url(main_url, additional_url, timeout=10, max_redirects=10):
    result = {
        "основной_url": main_url,
        "дополнительный_url": additional_url,
        "финальный_url": "",
        "код_статуса": None,
        "работает": False,
        "причина": "",
        "есть_контент": False,
        "маршрут_редиректов": [],
        "подробности_редиректов": [],
        "ответ_страницы": "",
    }

    try:
        redirect_info = manually_follow_redirects(
            additional_url, max_redirects=max_redirects, timeout=timeout
        )

        result["финальный_url"] = redirect_info["final_url"]
        result["код_статуса"] = redirect_info["final_status_code"]
        result["ответ_страницы"] = redirect_info["content"]
        result["маршрут_редиректов"] = [r["url"] for r in redirect_info["redirects"]]
        result["подробности_редиректов"] = redirect_info["redirects"]

        if redirect_info["content"] and (
            "<html" in redirect_info["content"].lower()
            or "<body" in redirect_info["content"].lower()
        ):
            result["есть_контент"] = True

        main_domain = urlparse(main_url).netloc.replace("www.", "")
        final_domain = urlparse(redirect_info["final_url"]).netloc.replace("www.", "")
        domains_match = main_domain == final_domain

        if (
            redirect_info["final_status_code"]
            and 200 <= redirect_info["final_status_code"] < 400
        ):
            result["работает"] = True
            if not domains_match:
                result["работает"] = False
                result["причина"] = (
                    f"Домен финального URL не совпадает с основным ({final_domain} vs {main_domain})"
                )
        elif (
            redirect_info["final_status_code"]
            and 400 <= redirect_info["final_status_code"] < 500
        ):
            if result["есть_контент"] and domains_match:
                result["работает"] = True
                result["причина"] = (
                    f"HTTP Ошибка {redirect_info['final_status_code']}, но страница загрузилась (домены совпадают)"
                )
            else:
                result["причина"] = f"HTTP Ошибка {redirect_info['final_status_code']}"
        elif (
            redirect_info["final_status_code"]
            and 500 <= redirect_info["final_status_code"] < 600
        ):
            result["причина"] = f"Серверная ошибка {redirect_info['final_status_code']}"
        elif redirect_info["max_redirects_reached"]:
            result["причина"] = (
                f"Превышено максимальное количество редиректов ({max_redirects})"
            )
        else:
            if "error" in redirect_info["redirects"][-1]:
                result["причина"] = f"Ошибка: {redirect_info['redirects'][-1]['error']}"
            else:
                result["причина"] = "Неизвестная ошибка"

    except Exception as e:
        result["причина"] = f"Неожиданная ошибка: {str(e)}"

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
        time.sleep(random.uniform(1.5, 3.5))
    return results


def save_results(
    results,
    output_file="результаты_проверки_url.csv",
    full_output_file="полные_результаты_проверки.json",
):
    df_data = []
    for result in results:
        row = {
            "Основной URL": result["основной_url"],
            "Начальный URL": result["дополнительный_url"],
            "Финальный URL": result["финальный_url"],
            "Код статуса": result["код_статуса"],
            "Работает": result["работает"],
            "Причина": result["причина"],
            "Есть контент": result["есть_контент"],
            "Кол-во редиректов": (
                len(result["маршрут_редиректов"]) - 1
                if result["маршрут_редиректов"]
                else 0
            ),
        }
        df_data.append(row)

    df = pd.DataFrame(df_data)
    df.to_csv(output_file, index=False)

    with open(full_output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return df


def load_urls_from_csv(file_path):
    try:
        df = pd.read_csv(file_path, sep=";")
    except:
        try:
            df = pd.read_csv(file_path, sep=",")
        except:
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
    if "URL" in df.columns and "ClickUrl" in df.columns:
        test_urls = list(zip(df["URL"], df["ClickUrl"]))
    else:
        url_columns = [
            col for col in df.columns if "url" in col.lower() or "ссылк" in col.lower()
        ]
        if len(url_columns) >= 2:
            test_urls = list(zip(df[url_columns[0]], df[url_columns[1]]))
        elif len(url_columns) == 1:
            test_urls = list(zip(df[url_columns[0]], df[url_columns[0]]))
        else:
            test_urls = list(
                zip(df.iloc[:, 0], df.iloc[:, 1] if df.shape[1] > 1 else df.iloc[:, 0])
            )
    return test_urls


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = "shop_export for test.csv"

    try:
        test_urls = load_urls_from_csv(csv_file)
        print(f"Загружено {len(test_urls)} URL из файла {csv_file}")
        results = process_urls(test_urls)
        df = save_results(results)
        print("\nРезультаты (основные):")
        print(df.to_string())
        print("\nПолные результаты сохранены в файл 'полные_результаты_проверки.json'")
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
