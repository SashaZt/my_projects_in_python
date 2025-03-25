import asyncio
import json
import os
import platform
import sys
from pprint import pprint

import nodriver as uc


async def main(login_input, password_input):
    browser = None
    page = None
    try:
        # Настраиваем опции в зависимости от ОС
        print(f"Определена операционная система: {platform.system()}")
        browser_args = []

        # На Linux может потребоваться дополнительные аргументы
        if platform.system() == "Linux":
            browser_args.extend(
                ["--no-sandbox", "--disable-dev-shm-usage", "--headless=new"]
            )
            print("Добавлены Linux-специфичные аргументы браузера")

        # Открываем браузер с аргументами, специфичными для ОС
        print("Запускаем браузер...")
        browser_args = ["--headless=new"]
        browser = await uc.start(headless=False, browser_args=browser_args)
        if not browser:
            raise ValueError("Не удалось инициализировать браузер")
        print("Браузер успешно запущен")

        # Переходим на страницу
        print("Переходим на страницу логина...")
        page = await browser.get("https://lardi-trans.com/ru/accounts/login/")
        if not page:
            raise ValueError("Не удалось загрузить страницу")
        print("Страница успешно загружена")

        # Ждем загрузки
        await asyncio.sleep(5)
        print("Ищем чекбокс...")
        checkbox = await page.select("div.passport-checkbox__icon")
        if checkbox:
            await checkbox.click()
            print("Чекбокс найден и нажат")
        else:
            print("Чекбокс не найден")

        # Находим поле логина
        print("Ищем поле логина...")
        login_field = await page.select(
            "body > div.passport > main > div > div > form > div:nth-child(2) > div > div > input"
        )
        if login_field:
            await login_field.send_keys(login_input)
            print("Логин успешно введен")
        else:
            print("Не удалось найти поле логина")
            html = await page.get_content()
            if html:
                print("HTML страницы:", html[:500])
            else:
                print("Не удалось получить HTML страницы")

        # Поле пароля
        print("Ищем поле пароля...")
        password_field = await page.wait_for('input[type="password"]', timeout=10)
        if password_field:
            await password_field.send_keys(password_input)
            print("Пароль успешно введен")
        else:
            print("Поле пароля не найдено")

        # Кнопка входа
        print("Ищем кнопку входа...")
        login_button = await page.wait_for('button[type="submit"]', timeout=10)
        if login_button:
            await login_button.click()
            print("Кнопка Войти нажата")
        else:
            print("Кнопка Войти не найдена")

        # Ждем авторизации
        print("Ждем завершения авторизации...")
        await asyncio.sleep(10)

        # Получаем куки через CDP для основного домена
        print("Получаем куки...")
        cookies = await page.send(
            uc.cdp.network.get_cookies(urls=["https://lardi-trans.com/"])
        )
        if cookies:
            cookies_json = [cookie.to_json() for cookie in cookies]
            # Сохраняем куки в JSON-файл с учетом платформы
            file_path = os.path.join(os.getcwd(), "cookies.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(cookies_json, f, ensure_ascii=False, indent=4)
            print(f"Куки успешно сохранены в {file_path}")
            return cookies_json
        else:
            print("Не удалось получить куки")
            current_url = page.url
            print(f"Текущий URL: {current_url}")
            return None

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        import traceback

        traceback.print_exc()
        return None
    finally:
        print("Завершение и освобождение ресурсов...")
        # Правильное закрытие ресурсов
        if page:
            try:
                print("Закрываем страницу...")
                await page.aclose()  # Используем aclose вместо close
                print("Страница закрыта")
            except Exception as e:
                print(f"Ошибка при закрытии страницы: {e}")

        # Browser в nodriver не имеет метода close()
        # Останавливаем процесс браузера, если он активен
        if browser and hasattr(browser, "stop"):
            try:
                print("Останавливаем браузер...")
                browser.stop()  # Для Browser используем stop() вместо close()
                print("Браузер остановлен")
            except Exception as e:
                print(f"Ошибка при остановке браузера: {e}")


if __name__ == "__main__":
    print("Скрипт запущен")

    # Защита от случайной утечки учетных данных в логи
    for i, arg in enumerate(sys.argv):
        if i > 0:  # Пропускаем имя скрипта
            print(f"Аргумент {i}: {'*' * len(arg)}")

    # Проверяем, переданы ли аргументы
    if len(sys.argv) != 3:
        print("Использование: python main.py <логин> <пароль>")
        sys.exit(1)

    # Получаем логин и пароль из аргументов командной строки
    login = sys.argv[1]
    password = sys.argv[2]
    print(f"Аргументы получены: {login}, {'*' * len(password)}")

    try:
        # Используем uc.loop() для запуска
        print("Запускаем процесс логина через uc.loop()...")

        # На Linux может потребоваться установить переменную среды для Chrome
        if platform.system() == "Linux":
            os.environ["DISPLAY"] = ":0"
            print("Установлена переменная DISPLAY для Linux")

        cookies = uc.loop().run_until_complete(main(login, password))
        print("Процесс логина завершен успешно")
    except KeyboardInterrupt:
        print("Процесс был прерван пользователем")
    except Exception as e:
        print(f"Критическая ошибка при выполнении: {e}")
        import traceback

        traceback.print_exc()

    print("Скрипт завершает работу")
    # Явно завершаем процесс
    sys.exit(0)
