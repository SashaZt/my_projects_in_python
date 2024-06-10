import time
import asyncio
import requests
import selenium
import os
import aiofiles
import json
import socks
import socket
import argparse
import sys

from seleniumwire import webdriver

from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
repuve_path = os.path.join(temp_path, "repuve")
pgj_path = os.path.join(temp_path, "pgj")
ocra_path = os.path.join(temp_path, "ocra")
carfax_path = os.path.join(temp_path, "carfax")
aviso_path = os.path.join(temp_path, "aviso")


# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(repuve_path, exist_ok=True)
os.makedirs(pgj_path, exist_ok=True)
os.makedirs(ocra_path, exist_ok=True)
os.makedirs(carfax_path, exist_ok=True)
os.makedirs(aviso_path, exist_ok=True)


def save_response_json(json_response, number, path):
    """Синхронно сохраняет JSON-данные в файл."""
    filename = os.path.join(path, f"{number}.json")
    with open(filename, mode="w", encoding="utf-8") as f:
        json.dump(json_response, f, ensure_ascii=False, indent=4)
    print(filename)


def load_config():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config.json")
    if not os.path.exists(filename_config):
        print("Нету файла с прокси-серверами!!!!!!!!!!!!!!!!!!!!!!!!!")
        sys.exit(1)  # Завершаем выполнение скрипта с кодом ошибки 1
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)

        return config


def main(number):
    time_wait = 60
    config = load_config()
    proxy = config.get("proxy", {})
    should_run_locally = (
        False  # Переменная для выбора режима запуска (локально или удаленно)
    )

    if should_run_locally:
        # Опции для локального запуска Chrome
        options = Options()
        options.add_experimental_option(
            "detach", True
        )  # Оставлять браузер открытым после выполнения скрипта
        options.page_load_strategy = "eager"  # Стратегия загрузки страницы (быстрая)

        # Инициализация драйвера для локального запуска
        driver = webdriver.Chrome(
            service=ChromeService(
                ChromeDriverManager().install()
            ),  # Установка ChromeDriver
            options=options,
        )
    else:
        # Настройка Selenium Wire с прокси SOCKS5
        sw_options = {
            "addr": "127.0.0.1",
            "auto_config": False,
            "port": 8091,
            "proxy": {
                "http": proxy,
                "https": proxy,
                "no_proxy": "localhost,127.0.0.1",  # Блокирует проксирование для локальных адресов
            },
        }

        # Опции для Chrome
        chrome_options = Options()
        # Установка стратегии загрузки страницы
        chrome_options.page_load_strategy = "eager"
        chrome_options.add_argument("--proxy-server=host.docker.internal:8091")
        # Игнорирование ошибок сертификатов
        chrome_options.add_argument("--ignore-certificate-errors")

        """Отключение загрузки изображений и других типов контента"""
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Отключение загрузки изображений
            "profile.managed_default_content_settings.stylesheets": 2,  # Отключение загрузки стилей (CSS)
            "profile.managed_default_content_settings.cookies": 2,  # Отключение сохранения и использования cookies
            # "profile.managed_default_content_settings.javascript": 2,  # Отключение выполнения JavaScript
            "profile.managed_default_content_settings.plugins": 2,  # Отключение загрузки плагинов
            "profile.managed_default_content_settings.popups": 2,  # Отключение всплывающих окон
            "profile.managed_default_content_settings.geolocation": 2,  # Отключение доступа к геолокации
            "profile.managed_default_content_settings.media_stream": 2,  # Отключение доступа к медиа-стримам (видео/аудио)
        }

        chrome_options.add_experimental_option("prefs", prefs)

        # Инициализация драйвера для удаленного запуска
        driver = webdriver.Remote(
            command_executor="http://127.0.0.1:4444/wd/hub",  # Адрес удаленного сервера Selenium
            options=chrome_options,
            seleniumwire_options=sw_options,  # Опции Selenium Wire
        )

    # Запускаем удаллено Selenium
    try:
        driver.implicitly_wait(time_wait)  # Установка неявного ожидания на 10 секунд
        # driver.set_page_load_timeout(30)  # Установка таймаута для загрузки страницы
        driver.maximize_window()  # Максимизация окна браузера

        # Переход на заданный URL
        driver.get("https://www2.repuve.gob.mx:8443/ciudadania/")
        time.sleep(1)
        # Определяем локатор для элемента
        locator_entendido = (
            By.CSS_SELECTOR,
            ".swal2-styled.swal2-default-outline",
        )
        first_element_found = False
        while not first_element_found:
            try:
                # Ждем, пока элемент станет доступным
                element_entendido = WebDriverWait(driver, time_wait).until(
                    ec.presence_of_element_located(locator_entendido)
                )
                first_element_found = True
            except selenium.common.exceptions.TimeoutException:
                driver.get("https://www2.repuve.gob.mx:8443/ciudadania/")
                element_entendido = WebDriverWait(driver, time_wait).until(
                    ec.presence_of_element_located(locator_entendido)
                )

        # Нажимаем на элемент
        element_entendido.click()
        time.sleep(1)
        # Определяем локатор для нового элемента
        locator_numero_de_placa = (
            By.CSS_SELECTOR,
            "div:nth-child(3) > div:nth-child(1) > input",
        )

        # Ждем, пока элемент станет доступным
        input_numero_de_placa = WebDriverWait(driver, time_wait).until(
            ec.presence_of_element_located(locator_numero_de_placa)
        )
        time.sleep(1)
        input_numero_de_placa.send_keys(number)

        # Определяем локатор для нового элемента
        locator_buscar = (
            By.CSS_SELECTOR,
            "div.clearfix > form > div > button.btn.btn-primary",
        )
        time.sleep(1)
        # Ждем, пока элемент станет доступным
        button_buscar = WebDriverWait(driver, time_wait).until(
            ec.presence_of_element_located(locator_buscar)
        )

        # Делаем клик на найденный элемент
        button_buscar.click()
        # Ждем появления следующего элемента
        locator_next_element = (
            By.CSS_SELECTOR,
            "div:nth-child(1) > div > ul > li.active > a",
        )

        element_found = False
        while not element_found:
            try:
                WebDriverWait(driver, time_wait).until(
                    ec.presence_of_element_located(locator_next_element)
                )
                element_found = True
            except selenium.common.exceptions.TimeoutException:
                driver.get("https://www2.repuve.gob.mx:8443/ciudadania/")
                time.sleep(5)
                locator_entendido = (
                    By.CSS_SELECTOR,
                    ".swal2-styled.swal2-default-outline",
                )

                # Ждем, пока элемент станет доступным
                element_entendido = WebDriverWait(driver, time_wait).until(
                    ec.presence_of_element_located(locator_entendido)
                )

                # Нажимаем на элемент
                element_entendido.click()
                # Определяем локатор для нового элемента
                locator_numero_de_placa = (
                    By.CSS_SELECTOR,
                    "div:nth-child(3) > div:nth-child(1) > input",
                )

                # Ждем, пока элемент станет доступным
                input_numero_de_placa = WebDriverWait(driver, time_wait).until(
                    ec.presence_of_element_located(locator_numero_de_placa)
                )
                # Повторяем действия снова
                input_numero_de_placa.send_keys(number)
                locator_buscar = (
                    By.CSS_SELECTOR,
                    "div.clearfix > form > div > button.btn.btn-primary",
                )
                time.sleep(1)
                # Ждем, пока элемент станет доступным
                button_buscar = WebDriverWait(driver, time_wait).until(
                    ec.presence_of_element_located(locator_buscar)
                )
                button_buscar.click()
        time.sleep(2)
        button_pgj_element = (
            By.CSS_SELECTOR,
            "div.col-sm-12 > div > div > div:nth-child(1) > div > ul > li:nth-child(2) > a",
        )
        button_pgj = WebDriverWait(driver, time_wait).until(
            ec.presence_of_element_located(button_pgj_element)
        )
        button_pgj.click()
        time.sleep(1)
        button_ocra_element = (
            By.CSS_SELECTOR,
            "div.col-sm-12 > div > div > div:nth-child(1) > div > ul > li:nth-child(3) > a",
        )
        button_ocra = WebDriverWait(driver, time_wait).until(
            ec.presence_of_element_located(button_ocra_element)
        )
        button_ocra.click()
        time.sleep(1)
        button_carfax_element = (
            By.CSS_SELECTOR,
            "div.col-sm-12 > div > div > div:nth-child(1) > div > ul > li:nth-child(4) > a",
        )
        button_carfax = WebDriverWait(driver, time_wait).until(
            ec.presence_of_element_located(button_carfax_element)
        )
        button_carfax.click()
        time.sleep(1)
        button_aviso_element = (
            By.CSS_SELECTOR,
            "div.col-sm-12 > div > div > div:nth-child(1) > div > ul > li:nth-child(5) > a",
        )
        button_aviso = WebDriverWait(driver, time_wait).until(
            ec.presence_of_element_located(button_aviso_element)
        )
        button_aviso.click()
        time.sleep(2)
        # Обработка запросов
        url_to_path = {
            "https://www2.repuve.gob.mx:8443/consulta/consulta/repuve": repuve_path,
            "https://www2.repuve.gob.mx:8443/consulta/consulta/pgj": pgj_path,
            "https://www2.repuve.gob.mx:8443/consulta/consulta/ocra": ocra_path,
            "https://www2.repuve.gob.mx:8443/consulta/consulta/carfax": carfax_path,
            "https://www2.repuve.gob.mx:8443/consulta/consulta/aviso": aviso_path,
        }

        for request in driver.requests:
            if request.url in url_to_path:
                try:
                    if (
                        request.response
                        and "application/json"
                        in request.response.headers.get("Content-Type", "")
                    ):
                        json_response = json.loads(
                            request.response.body.decode("utf-8")
                        )
                        path = url_to_path[request.url]
                        save_response_json(json_response, number, path)
                except Exception as e:
                    print(f"Error processing request {request.url}: {e}")

    finally:
        # Закрытие драйвера и завершение сеанса
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to run with a specific number parameter."
    )
    parser.add_argument("number", type=str, help="The number to be used in the script")
    args = parser.parse_args()

    asyncio.run(main(args.number))
