import json
import os
import platform
import random
import shutil
import time
from datetime import datetime
from pathlib import Path

import requests
from config.logger import logger


def get_random_pause(min_seconds, max_seconds):
    """
    Возвращает случайное число секунд для паузы в заданном диапазоне

    Args:
        min_seconds (int/float): Минимальное количество секунд
        max_seconds (int/float): Максимальное количество секунд

    Returns:
        float: Случайное число секунд для паузы

    Examples:
        >>> pause = get_random_pause(2, 5)
        >>> print(f"Пауза: {pause:.2f} секунд")

        >>> # Использование с time.sleep
        >>> time.sleep(get_random_pause(1, 3))

        >>> # Использование с asyncio.sleep
        >>> await asyncio.sleep(get_random_pause(0.5, 2.0))
    """
    if min_seconds > max_seconds:
        min_seconds, max_seconds = max_seconds, min_seconds
        logger.warning(f"⚠️ Поменял местами min и max: {min_seconds} - {max_seconds}")

    if min_seconds < 0:
        min_seconds = 0
        logger.warning(
            "⚠️ Минимальная пауза не может быть отрицательной, установлена в 0"
        )

    pause_duration = random.uniform(min_seconds, max_seconds)
    logger.debug(f"🎲 Случайная пауза: {pause_duration:.2f} секунд")

    return pause_duration


def random_pause(min_seconds, max_seconds):
    """
    Асинхронная функция: выполняет случайную паузу в заданном диапазоне

    Args:
        min_seconds (int/float): Минимальное количество секунд
        max_seconds (int/float): Максимальное количество секунд

    Examples:
        >>> await async_random_pause(1, 3)  # Асинхронная пауза от 1 до 3 секунд
        >>> await async_random_pause(2.5, 5.0)  # Асинхронная пауза от 2.5 до 5 секунд
    """
    pause_duration = get_random_pause(min_seconds, max_seconds)
    logger.info(f"😴 Асинхронная пауза {pause_duration:.2f} секунд...")
    time.sleep(pause_duration)


def get_downloads_folder():
    """
    Получает путь к папке загрузок пользователя на Windows, macOS и Linux.

    Returns:
        Path: Путь к папке загрузок или None, если не удается определить
    """
    system = platform.system()

    try:
        if system == "Windows":
            # Windows: используем переменную окружения USERPROFILE
            userprofile = os.environ.get("USERPROFILE")
            if userprofile:
                downloads_path = Path(userprofile) / "Downloads"
                if downloads_path.exists():
                    return downloads_path

        elif system == "Darwin":  # macOS
            # macOS: папка загрузок в домашней директории пользователя
            home = Path.home()
            downloads_path = home / "Downloads"
            if downloads_path.exists():
                return downloads_path

        elif system == "Linux":
            # Linux: сначала пробуем XDG_DOWNLOAD_DIR, затем ~/Downloads
            xdg_download = os.environ.get("XDG_DOWNLOAD_DIR")
            if xdg_download:
                downloads_path = Path(xdg_download)
                if downloads_path.exists():
                    return downloads_path

            # Если XDG не задан, используем стандартную папку
            home = Path.home()
            downloads_path = home / "Downloads"
            if downloads_path.exists():
                return downloads_path

        # Fallback: пробуем стандартную папку Downloads в домашней директории
        fallback_path = Path.home() / "Downloads"
        if fallback_path.exists():
            return fallback_path

    except Exception as e:
        logger.error(f"Ошибка при определении папки загрузок: {e}")

    return None


def get_cookies_folder():
    """Получает или создает папку для хранения куки"""
    current_directory = Path.cwd()
    cookies_dir = current_directory / "cookies"
    cookies_dir.mkdir(parents=True, exist_ok=True)
    return cookies_dir


def move_latest_cookie_to_cookies_folder(client_id):
    """Находит последний файл куки в Downloads и перемещает его в папку cookies"""
    downloads = get_downloads_folder()
    if not downloads or not downloads.exists():
        logger.error("Папка загрузок не найдена")
        return None

    pattern = f"cookie_{client_id}_01.json"
    matching_files = list(downloads.glob(pattern))

    if not matching_files:
        # Ищем любые файлы куки, если нет конкретных
        matching_files = list(downloads.glob("cookie_*.json"))
        if not matching_files:
            logger.error("Файлы куки не найдены в папке загрузок")
            return None

    # Получаем самый новый файл
    latest_cookie_file = max(matching_files, key=lambda p: p.stat().st_mtime)

    # Создаем целевую папку, если её нет
    cookies_folder = get_cookies_folder()

    target_path = cookies_folder / pattern

    try:
        # Копируем файл (не перемещаем, чтобы сохранить оригинал в загрузках)
        shutil.copy2(latest_cookie_file, target_path)
        logger.info(f"Файл куки скопирован из {latest_cookie_file} в {target_path}")
        return target_path
    except Exception as e:
        logger.error(f"Ошибка при копировании файла куки: {str(e)}")
        return None


def get_latest_cookie_from_cookies_folder(client_id):
    """Находит последний файл куки в папке cookies"""
    cookies_folder = get_cookies_folder()
    pattern = f"cookie_{client_id}_*.json"
    matching_files = list(cookies_folder.glob(pattern))

    if not matching_files:
        logger.error(f"Файлы куки не найдены в папке cookies для клиента {client_id}")
        return None

    # Получаем самый новый файл
    latest_cookie_file = max(matching_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Найден файл куки в папке cookies: {latest_cookie_file}")
    return latest_cookie_file


def load_cookies_from_file(file_path):
    """
    Загружает куки из JSON-файла и возвращает только необходимые куки
    в формате строки и словаря
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            cookie_data = json.load(f)

        # Получаем значения важных куки из словаря cookies
        important_cookies = {}
        if "cookies" in cookie_data:
            cookies_dict = cookie_data["cookies"]
            # Список важных куки, которые мы хотим получить
            important_keys = [
                "_cmuid",
                "gdpr_permission_given",
                "QXLSESSID",
                "datadome",
            ]

            for key in important_keys:
                if key in cookies_dict:
                    important_cookies[key] = cookies_dict[key]

        # Если важные куки не найдены в словаре, попробуем извлечь их из строки cookieString
        if not important_cookies and "cookieString" in cookie_data:
            cookie_str = cookie_data["cookieString"]
            cookie_parts = cookie_str.split("; ")

            for part in cookie_parts:
                if "=" in part:
                    name, value = part.strip().split("=", 1)
                    if name in [
                        "_cmuid",
                        "gdpr_permission_given",
                        "QXLSESSID",
                        "datadome",
                    ]:
                        important_cookies[name] = value

        # Формируем строку для заголовка Cookie
        cookie_string = "; ".join(
            [f"{name}={value}" for name, value in important_cookies.items()]
        )

        logger.info(f"Загружены важные куки: {', '.join(important_cookies.keys())}")

        return {"cookieString": cookie_string, "cookies": important_cookies}
    except Exception as e:
        logger.error(f"Ошибка при загрузке куки из файла {file_path}: {str(e)}")
        return None


def create_ad_campaign(
    cookies_data,
    client_id,
    campaign_name,
    ad_group_name,
    daily_limit,
    max_cpc,
    offer_id,
    start_date,
    end_date,
):
    """Создает рекламную кампанию в Allegro"""

    # URL API
    url = f"https://edge.salescenter.allegro.com/ads-panel/api/clients/{client_id}/campaigns"

    # Полные заголовки, как в curl-запросе
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
        "Cookie": cookies_data["cookieString"],
    }

    # Данные для создания кампании
    payload = {
        "campaign": {"name": campaign_name, "type": "GENERIC"},
        "adGroup": {
            "name": ad_group_name,
            "dailyLimit": daily_limit,
            "startDateTime": start_date,
            "endDateTime": end_date,
            "maxCpc": max_cpc,
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

    # Логирование запроса для отладки
    logger.info(f"Отправка запроса на URL: {url}")
    # logger.info(f"Данные: {json.dumps(payload, indent=4)}")

    # Проверяем куки перед отправкой
    if "QXLSESSID" not in cookies_data["cookieString"]:
        logger.error("В файле куки отсутствует QXLSESSID!")
        # Выводим часть строки куки для диагностики
        logger.error(
            f"Строка куки (первые 100 символов): {cookies_data['cookieString'][:100]}"
        )
        return None

    # Выполняем запрос
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        # Проверяем статус ответа
        if response.status_code in [200, 201]:
            logger.info(f"Успешно создана рекламная кампания: {campaign_name}")
            return response.json()
        else:
            logger.error(f"Ошибка при создании кампании: {response.status_code}")
            logger.error(f"Ответ сервера: {response.text}")

            return None
    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        return None


def main():
    current_directory = Path.cwd()
    ad_directory = current_directory / "ad"
    ad_directory.mkdir(parents=True, exist_ok=True)
    output_json_file = ad_directory / "test.json"

    # Загрузка конфигурации
    try:
        with open(output_json_file, "r", encoding="utf-8") as f:
            configs = json.load(f)
        logger.info(f"Конфигурация успешно загружена из файла: {output_json_file}")
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации: {str(e)}")
        return
    for config in configs:
        # ID клиента (из URL)
        client_id = config.get("client_id", "MTMwNzU2NDgwAA")

        # Параметры кампании
        campaign_name = config.get("campaign_name", "test_24")
        ad_group_name = config.get("ad_group_name", "Grupa reklam - 14.05.2025")
        daily_limit = config.get("daily_limit", "140.00")
        max_cpc = config.get("max_cpc", "0.70")
        offer_id = config.get("offer_id", "17475780478")
        start_date = config.get("start_date", "2025-05-14T22:00:00.000Z")
        end_date = config.get("end_date", "2025-05-14T22:00:00.000Z")

        # Сначала проверяем, есть ли свежий файл куки в папке cookies
        cookie_file = get_latest_cookie_from_cookies_folder(client_id)

        # Если нет файла в папке cookies или он старый, ищем в папке загрузок и копируем новый
        if (
            not cookie_file
            or (
                datetime.now() - datetime.fromtimestamp(cookie_file.stat().st_mtime)
            ).total_seconds()
            > 3600
        ):
            logger.info("Поиск свежего файла куки в папке загрузок...")
            new_cookie_file = move_latest_cookie_to_cookies_folder(client_id)
            if new_cookie_file:
                cookie_file = new_cookie_file
            else:
                logger.warning(
                    "Не удалось найти свежий файл куки, используем существующий"
                )

        if not cookie_file:
            logger.error("Файл куки не найден!")
            return

        # Загружаем данные из файла
        cookies_data = load_cookies_from_file(cookie_file)
        if not cookies_data:
            logger.error("Не удалось загрузить данные из файла куки")
            return
        # Создаем кампанию
        result = create_ad_campaign(
            cookies_data=cookies_data,
            client_id=client_id,
            campaign_name=campaign_name,
            ad_group_name=ad_group_name,
            daily_limit=daily_limit,
            max_cpc=max_cpc,
            offer_id=offer_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Сохраняем результат в файл для отладки
        if result:
            result_file = ad_directory / f"campaign_result_{offer_id}.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            logger.info(f"Результат сохранен в файл: {result_file}")
            random_pause(1, 5)
        else:
            logger.error("Не удалось создать рекламную кампанию.")


if __name__ == "__main__":
    main()
