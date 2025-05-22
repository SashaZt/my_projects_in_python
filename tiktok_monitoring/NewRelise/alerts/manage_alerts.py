#!/usr/bin/env python3
"""
Скрипт с основными функциями для работы с TikTok Alerts API.
Включает три основные функции:
1. Создание алерта
2. Получение списка алертов
3. Подписка на алерт

Каждая функция сохраняет результаты запросов в JSON-файлы.
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict

import requests
from config.logger import logger

# Базовые настройки
TIKTOK_API_BASE_URL = "https://tiktok.eulerstream.com"
TIKTOK_API_KEY = (
    "YWZiMjlhZjljNWZlZmExODkyMTM1N2RjOTAyNTczZjBmZjE2OGQ3ZTJlMzIwZDg2OGVhMzdh"
)
TIKTOK_ACCOUNT_ID = 669

# Директория для сохранения результатов API запросов
API_RESPONSES_DIR = "api_responses"
os.makedirs(API_RESPONSES_DIR, exist_ok=True)

# Базовые заголовки для API запросов
HEADERS = {"accept": "application/json", "Content-Type": "application/json"}


def save_response_to_file(response_data: Dict[str, Any], operation: str) -> str:
    """Сохраняет ответ API в JSON-файл"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{API_RESPONSES_DIR}/{operation}_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(response_data, f, indent=4, ensure_ascii=False)

    logger.info(f"Ответ API сохранен в файл: {filename}")
    return filename


def extract_alert_info(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Извлекает основную информацию из данных алерта"""
    return {
        "id": alert_data.get("id"),
        "account_id": alert_data.get("account_id"),
        "created_at": alert_data.get("created_at"),
        "alert_creator_username": alert_data.get("alert_creator_username"),
        "alert_creator_id": alert_data.get("alert_creator_id"),
    }


def create_alert(unique_id: str) -> Dict[str, Any]:
    """
    Функция 1: Создание нового алерта для TikTok аккаунта

    Аргументы:
        unique_id (str): Уникальный ID TikTok аккаунта (например, carry..ray)

    Возвращает:
        dict: Ответ API с информацией о созданном алерте
    """
    logger.info(f"\n[ФУНКЦИЯ 1] Создание алерта для {unique_id}...\n")
    params = {
        "apiKey": "YWZiMjlhZjljNWZlZmExODkyMTM1N2RjOTAyNTczZjBmZjE2OGQ3ZTJlMzIwZDg2OGVhMzdh",
    }

    json_data = {
        "unique_id": unique_id,
    }
    url = "https://tiktok.eulerstream.com/accounts/669/alerts/create"
    try:
        response = requests.put(
            url,
            params=params,
            headers=HEADERS,
            json=json_data,
            timeout=30,
        )
        response.raise_for_status()

        # Получаем ответ
        response_data = response.json()

        # Сохраняем ответ в файл
        save_response_to_file(response_data, "create_alert")

        logger.info("\nОтвет API:")
        logger.info(json.dumps(response_data, indent=4, ensure_ascii=False))

        return response_data

    except Exception as e:
        error_data = {"error": str(e)}
        save_response_to_file(error_data, "create_alert_error")
        logger.error(f"\nОшибка: {str(e)}")
        return error_data


def get_alerts() -> Dict[str, Any]:
    """
    Функция 2: Получение списка всех алертов

    Возвращает:
        dict: Ответ API со списком всех алертов
    """
    logger.info("\n[ФУНКЦИЯ 2] Получение списка алертов...\n")

    url = f"{TIKTOK_API_BASE_URL}/accounts/{TIKTOK_ACCOUNT_ID}/alerts/list?apiKey={TIKTOK_API_KEY}"

    # Выводим информацию о запросе
    logger.info(f"URL: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        # Получаем ответ
        response_data = response.json()

        # Сохраняем ответ в файл
        save_response_to_file(response_data, "get_alerts")

        logger.info("\nОтвет API:")
        logger.info(json.dumps(response_data, indent=4, ensure_ascii=False))

        # Если есть алерты, извлекаем информацию о каждом
        if "alerts" in response_data and response_data["alerts"]:
            logger.info("\nИзвлеченная информация об алертах:")
            for alert in response_data["alerts"]:
                alert_info = extract_alert_info(alert)
                logger.info(json.dumps(alert_info, indent=4, ensure_ascii=False))

        return response_data

    except Exception as e:
        error_data = {"error": str(e)}
        save_response_to_file(error_data, "get_alerts_error")
        logger.error(f"\nОшибка: {str(e)}")
        return error_data


def subscribe_to_alert(alert_id: int, webhook_url: str) -> Dict[str, Any]:
    """
    Функция 3: Подписка на алерт

    Аргументы:
        alert_id (int): ID алерта для подписки
        webhook_url (str): URL для получения webhook-уведомлений

    Возвращает:
        dict: Ответ API с информацией о созданной подписке
    """
    logger.info(f"\n[ФУНКЦИЯ 3] Подписка на алерт {alert_id}...\n")

    url = f"{TIKTOK_API_BASE_URL}/accounts/{TIKTOK_ACCOUNT_ID}/alerts/{alert_id}/targets/create?apiKey={TIKTOK_API_KEY}"
    payload = {"url": webhook_url}

    # Выводим информацию о запросе
    logger.info(f"URL: {url}")
    logger.info(f"Payload: {json.dumps(payload, indent=4)}")

    try:
        response = requests.put(url, headers=HEADERS, json=payload, timeout=10)
        response.raise_for_status()

        # Получаем ответ
        response_data = response.json()

        # Сохраняем ответ в файл
        save_response_to_file(response_data, "subscribe_to_alert")

        logger.info("\nОтвет API:")
        logger.info(json.dumps(response_data, indent=4, ensure_ascii=False))

        return response_data

    except Exception as e:
        error_data = {"error": str(e)}
        save_response_to_file(error_data, "subscribe_to_alert_error")
        logger.error(f"\nОшибка: {str(e)}")
        return error_data


def main():
    unique_ids = [
        # "adele_bliss_",
        # "alba.zhu",
        # "aleksa.bloom",
        # "aleksa.wonder",
        # "alessandrinaa",
        # "alexa_faiiry",
        # "alexandra.velour",
        # "alina.byte",
        # "almavivva",
        # "anet.velvet",
        # "angeel.darii",
        # "anna_bo01",
        # "anna.cheerr",
        # "ann.pluushko",
        # "annrosse_",
        # "berry_kerri",
        # "blonde_rapunzel",
        # "blondieegirrl",
        # "bz.inna",
        # "carry..ray",
        # "cassaandraa_21",
        # "chereshnyyaaa",
        # "cherrybliss23",
        # "cutiefoxx",
        # "daikirimar",
        # "daria.luxe",
        # "daria.zen",
        # "dari.echo",
        # "dariia.lx",
        # "dariiiaaa_yeet",
        # "dary.fervy",
        # "ddomikss",
        # "diana_staarr",
        # "dii_peach",
        # "diixxxii",
        # "disco.yumi",
        # "doc_vita",
        # "eliza_bethix",
        # "elya_marchyshyna",
        # "exxlissyy",
        # "fllora_vans",
        "gh.kisa",
        "i.am.dian",
        "illlexs.m",
        "iluha_bitsuhaa",
        "imvalerie_mua",
        "ira_angell",
        "ira_sparkle",
        "juliaa.eclipse",
        "juliaa.starrr",
        "kary_ice",
        "kate__mooon",
        "katrr.yyyyy",
        "khaleesi_garcia",
        "koi_princesss",
        "kriiissyk",
        "kristiina_dazzle",
        "kris.tina.coconut",
        "kristinakvk",
        "lina.mystic",
        "lizzyyy0",
        "llilidiaa",
        "lolita.dreamss",
        "luna_pulsee",
        "luryshaa",
        "margo.cute",
        "maviennee",
        "meseddaaa",
        "mila_brunette",
        "miss__katty",
        "mmariaviva",
        "mousenyya",
        "ms88m",
        "_murrtime_",
        "nassteyst",
        "nastyaa_pixel",
        "nasty.euphoria",
        "niika.verse",
        "oana_musee",
        "oops.nastya",
        "polly_bunny",
        "polyannnaa.sweetie",
        "princess_anna00",
        "rariity_fly",
        "sashalixxx",
        "sergiiivnaa",
        "skinny.hamsterrrr",
        "solomiya.flo",
        "solyaa_a",
        "spicyy.ksu",
        "stasiaxoo",
        "sweetie.pollyy",
        "tomachhka",
        "tomekovch",
        "tori.nilson",
        "torrolli",
        "ttiana_lexis",
        "vallerii_vall",
        "viki_stellar",
        "visstasia",
        "vveronaas",
        "vvv.maryyy",
        "yana.skyy",
        "yuliadreamer",
        "yulia_spark",
        "yulia_sunshinee",
        "zaretskaya.anna",
        "milanss_love_up",
        "yulchik.pups",
        "sweetie.pollyy",
        "liliiiiiiiiiiia",
        "darla_wow",
        "daryyspace",
        "arinafoxxy",
        "aylinka_mee",
        "darla_wow",
        "daryyspace",
        "__ana.steysha",
        "_bby.dragon_",
        "kiraa_twilight",
        "aetorianova",
    ]
    # # unique_id = "imvalerie_mua"
    # for unique_id in unique_ids[:11]:

    #     create_alert(unique_id)
    #     time.sleep(10)

    # get_alerts()
    for alert_id in range(128, 138):

        webhook_url = "https://tikspy.cc/webhook"
        subscribe_to_alert(alert_id, webhook_url)
        time.sleep(15)


if __name__ == "__main__":
    main()
