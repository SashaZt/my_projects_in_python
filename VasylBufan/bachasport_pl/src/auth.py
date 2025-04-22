import json
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup
from config.logger import logger

# Получаем текущую директорию и пути
current_directory = Path.cwd()
config_directory = current_directory / "config"
data_directory = current_directory / "data"
config_file = config_directory / "config.json"


def get_config() -> dict:
    """
    Загружает конфигурацию из JSON-файла.

    Returns:
        dict: Данные конфигурации.
    """
    try:
        with open(config_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        logger.error(f"Файл конфигурации не найден: {config_file}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Ошибка декодирования JSON в файле: {config_file}")
        raise


# Загрузка конфигурации
try:
    config = get_config()
    CONTRACTOR_CODE = config["site"]["contractor_code"]
    NAME = config["site"]["name"]
    PASSWORD = config["site"]["password"]
except (KeyError, FileNotFoundError, json.JSONDecodeError) as e:
    logger.critical(f"Ошибка при загрузке конфигурации: {e}")
    raise


def get_session() -> Optional[requests.Session]:
    """
    Авторизуется на сайте и возвращает активную сессию.

    Returns:
        Optional[requests.Session]: Сессия с авторизацией или None в случае ошибки.
    """
    try:
        # Создаем сессию
        session = requests.Session()

        # Сначала делаем GET запрос на страницу логина, чтобы получить актуальный токен
        initial_response = session.get("https://panel.bachasport.pl/login")
        if initial_response.status_code != 200:
            logger.error(
                f"Не удалось получить страницу логина: {initial_response.status_code}"
            )
            return None

        # Используем BeautifulSoup для извлечения токена из формы
        soup = BeautifulSoup(initial_response.text, "lxml")
        token_input = soup.find("input", {"name": "_token"})

        if not token_input or not token_input.get("value"):
            logger.error("Не удалось найти CSRF токен на странице логина")
            return None

        csrf_token = token_input.get("value")
        logger.info(f"Получен CSRF токен: {csrf_token[:10]}...")

        # Делаем POST запрос для авторизации с актуальным токеном
        login_url = "https://panel.bachasport.pl/login"
        login_payload = {
            "_token": csrf_token,
            "contractor_code": CONTRACTOR_CODE,
            "name": NAME,
            "password": PASSWORD,
        }

        login_headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://panel.bachasport.pl",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "referer": "https://panel.bachasport.pl/login",
        }

        # Авторизуемся на сайте и сохраняем куки в сессии
        response = session.post(login_url, data=login_payload, headers=login_headers)

        # Выводим cookies для диагностики
        logger.info(f"Полученные cookies: {dict(session.cookies)}")

        if response.status_code == 200:
            # Проверяем редирект - это основной индикатор успешной авторизации
            final_url = response.url
            logger.info(f"Итоговый URL после авторизации: {final_url}")

            if final_url != login_url and (
                "/start" in final_url or "/dashboard" in final_url
            ):
                logger.info(f"Успешный редирект на: {final_url}")

                # Проверяем наличие формы логина - если её нет, значит мы авторизованы
                soup = BeautifulSoup(response.text, "lxml")
                login_form = soup.find("form", {"action": login_url})

                if not login_form:
                    logger.info("Форма логина отсутствует - успешная авторизация.")

                    # Даже если не найдены явные индикаторы в DOM, но редирект был успешным,
                    # считаем авторизацию успешной
                    return session
                else:
                    logger.error(
                        "Форма логина все еще присутствует - авторизация не удалась."
                    )
            else:
                # Проверяем ошибку авторизации - ищем элементы с сообщениями об ошибках
                soup = BeautifulSoup(response.text, "lxml")
                error_elements = soup.find_all(
                    ["div", "span", "p"],
                    {"class": ["alert", "error", "danger", "invalid-feedback"]},
                )

                if error_elements:
                    for elem in error_elements:
                        if elem.text.strip():
                            logger.error(f"Сообщение об ошибке: {elem.text.strip()}")
                else:
                    logger.error("Не выполнен редирект после авторизации.")

                # Сохраняем HTML-страницу для анализа
                with open(
                    data_directory / "login_response.html", "w", encoding="utf-8"
                ) as f:
                    f.write(response.text)
                logger.info("HTML-ответ сохранен в login_response.html для анализа")
                return None
        else:
            logger.error(f"Ошибка при авторизации: статус {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сетевого запроса при авторизации: {e}")
        return None
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при авторизации: {e}")
        return None
