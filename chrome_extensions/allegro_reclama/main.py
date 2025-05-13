import json
import requests
import os
import time
from datetime import datetime, timedelta


def load_cookies(client_id):
    """Загрузка куки из файла"""
    cookies_path = f"C:/allegro/cookies_{client_id}.json"

    try:
        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies_data = json.load(f)
        print(f"Куки успешно загружены из файла: {cookies_path}")
        return cookies_data
    except FileNotFoundError:
        print(f"Файл куки не найден: {cookies_path}")
        return None
    except json.JSONDecodeError:
        print(f"Ошибка при парсинге JSON в файле: {cookies_path}")
        return None


def load_config():
    """Загрузка конфигурации из файла"""
    config_path = "C:/allegro/config.json"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        print(f"Конфигурация успешно загружена из файла: {config_path}")
        return config
    except FileNotFoundError:
        print(f"Файл конфигурации не найден: {config_path}")
        return []
    except json.JSONDecodeError:
        print(f"Ошибка при парсинге JSON в файле: {config_path}")
        return []


def launch_ad_campaign(
    client_id, cookies_data, offer_id="17475780478", campaign_name=None
):
    """Запуск рекламной кампании на Allegro"""
    # Базовый URL для API
    base_url = f"https://edge.salescenter.allegro.com/ads-panel/api/clients/{client_id}/campaigns"

    # Если имя кампании не указано, используем текущую дату и время
    if campaign_name is None:
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        campaign_name = f"campaign_{current_time}"

    # Дата запуска кампании (завтра в 22:00 UTC)
    tomorrow = datetime.now() + timedelta(days=1)
    start_date = (
        tomorrow.replace(hour=22, minute=0, second=0, microsecond=0).isoformat() + "Z"
    )

    # Формируем данные запроса
    payload = {
        "campaign": {"name": campaign_name, "type": "GENERIC"},
        "adGroup": {
            "name": f"Grupa reklam - {tomorrow.strftime('%d.%m.%Y')}",
            "dailyLimit": "140.00",
            "startDateTime": start_date,
            "maxCpc": "0.70",
            "placementIds": ["listing"],
            "model": {
                "type": "offers-placement-based-static",
                "offerIds": [offer_id],
                "phrases": {
                    "additionalKeywords": [],
                    "queryForbiddenPhrases": [],
                    "queryRequiredPhrases": [],
                },
            },
        },
    }

    # Заголовки запроса
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "DNT": "1",
        "DPR": "1",
        "Pragma": "no-cache",
        "Priority": "u=0, i",
        "Referer": "https://salescenter.allegro.com/ads/panel/campaigns?marketplace=allegro-pl",
        "Sec-CH-Device-Memory": "8",
        "Sec-CH-Prefers-Color-Scheme": "light",
        "Sec-CH-Prefers-Reduced-Motion": "reduce",
        "Sec-CH-UA": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "Sec-CH-UA-Arch": '"x86"',
        "Sec-CH-UA-Full-Version-List": '"Google Chrome";v="135.0.7049.115", "Not-A.Brand";v="8.0.0.0", "Chromium";v="135.0.7049.115"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Model": '""',
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-CH-Viewport-Height": "1031",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Viewport-Width": "1193",
        "Cookie": cookies_data["header"],
    }

    # Отправляем запрос
    try:
        response = requests.post(base_url, headers=headers, json=payload)

        # Проверяем статус ответа
        if response.status_code == 200 or response.status_code == 201:
            print(f"Реклама успешно запущена! Статус: {response.status_code}")
            print(f"Ответ сервера: {response.json()}")
            return True, response.json()
        else:
            print(f"Ошибка при запуске рекламы. Статус: {response.status_code}")
            print(f"Ответ сервера: {response.text}")
            return False, response.text
    except Exception as e:
        print(f"Произошла ошибка при отправке запроса: {str(e)}")
        return False, str(e)


def main():
    # Загружаем конфигурацию
    config = load_config()

    if not config:
        print("Не удалось загрузить конфигурацию. Завершаем работу.")
        return

    # Проходим по всем аккаунтам в конфигурации
    for account in config:
        client_id = account.get(
            "clientId_01"
        )  # Или другой ключ, в зависимости от структуры
        if not client_id:
            print(f"Пропускаем аккаунт, т.к. не указан clientId: {account}")
            continue

        print(f"\nОбрабатываем аккаунт с clientId: {client_id}")

        # Загружаем куки для этого аккаунта
        cookies_data = load_cookies(client_id)
        if not cookies_data:
            print(f"Не удалось загрузить куки для аккаунта {client_id}. Пропускаем.")
            continue

        # Проверяем время последнего изменения файла куки
        cookies_path = f"C:/allegro/cookies_{client_id}.json"
        if os.path.exists(cookies_path):
            file_age_seconds = time.time() - os.path.getmtime(cookies_path)
            file_age_hours = file_age_seconds / 3600

            if file_age_hours > 24:
                print(
                    f"Предупреждение: файл куки старше 24 часов ({file_age_hours:.1f} ч). Рекомендуется обновить куки."
                )

        # Запускаем рекламную кампанию
        success, result = launch_ad_campaign(client_id, cookies_data)

        if success:
            print(f"Реклама успешно запущена для аккаунта {client_id}")
        else:
            print(f"Не удалось запустить рекламу для аккаунта {client_id}")

        # Пауза между запросами для разных аккаунтов
        if client_id != config[-1].get("clientId_01"):  # Если это не последний аккаунт
            print("Ожидание 5 секунд перед обработкой следующего аккаунта...")
            time.sleep(5)


if __name__ == "__main__":
    main()
