import asyncio
import json
from pprint import pprint

import nodriver as uc
import requests

"""
 Настраиваем аргументы браузера
        # browser_args = ["--headless=new"]

        # # Открываем браузер
        # print("Запускаем браузер с --headless=new...")
        # browser = await uc.start(browser_args=browser_args)
        # Открываем браузер
"""


async def main():
    browser = None
    page = None
    try:
        # Настраиваем аргументы браузера открою в рабочей версии
        browser_args = ["--headless=new"]

        # Открываем браузер
        print("Запускаем браузер с --headless=new...")
        browser = await uc.start(browser_args=browser_args)
        # Открываем браузер
        # browser = await uc.start(headless=False)
        if not browser:
            raise ValueError("Не удалось инициализировать браузер")
        print("Браузер успешно запущен")

        # Переходим на страницу
        print("Переходим на страницу логина...")
        page = await browser.get("https://lardi-trans.com/ru/accounts/login/")
        if not page:
            raise ValueError("Не удалось загрузить страницу")

        # Ждем загрузки
        await asyncio.sleep(5)
        checkbox = await page.select("div.passport-checkbox__icon")
        if checkbox:
            await checkbox.click()

        # Находим поле логина
        print("Ищем поле логина...")
        login_input = await page.select(
            "body > div.passport > main > div > div > form > div:nth-child(2) > div > div > input"
        )
        if login_input:
            await login_input.send_keys("dmitrosivij1")
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
        password_input = await page.wait_for('input[type="password"]', timeout=10)
        if password_input:
            await password_input.send_keys("112233Q@")
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

        # Ждем авторизации (увеличиваем время)
        print("Ждем завершения авторизации...")
        await asyncio.sleep(10)

        # Получаем куки через CDP для основного домена
        print("Получаем куки...")
        cookies = await page.send(
            uc.cdp.network.get_cookies(urls=["https://lardi-trans.com/"])
        )
        if cookies:
            cookies_json = [cookie.to_json() for cookie in cookies]
            print("Полученные куки:")
            pprint(cookies_json)
            await asyncio.sleep(5)
            # Сохраняем куки в JSON-файл
            with open("cookies.json", "w", encoding="utf-8") as f:
                json.dump(cookies_json, f, ensure_ascii=False, indent=4)
            print("Куки сохранены в cookies.json")

        else:
            print("Не удалось получить куки")
            current_url = page.url
            print(f"Текущий URL: {current_url}")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
    finally:
        # Минимальная обработка закрытия
        if page:
            try:
                await page.close()
            except:
                pass


def get_post():
    # Читаем куки из файла
    with open("cookies.json", "r", encoding="utf-8") as f:
        cookies_list = json.load(f)

    # Извлекаем куки
    cookies = {cookie["name"]: cookie["value"] for cookie in cookies_list}

    # Добавляем cusg, если его нет
    if "cusg" not in cookies:
        cookies["cusg"] = "true"
        print("Добавлен отсутствующий ключ 'cusg'")

    print("Используемые куки:", cookies)

    # Выполняем POST-запрос
    url = "https://lardi-trans.com/webapi/proposal/my/search/gruz/published/"
    payload = {"page": 1, "size": 100}
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    response = requests.post(
        url, cookies=cookies, json=payload, headers=headers, timeout=30
    )
    print("Статус ответа:", response.status_code)
    print("Ответ сервера:", response.text)


def proverka():

    cookies = {
        "lardi_device": "6bc5fc44-0d6f-4f40-a99b-48cf857ae0df",
        "_gcl_au": "1.1.109641110.1742926017",
        "_fbp": "fb.1.1742926017585.4905652054973466",
        "__oagr": "true",
        "__utma": "81750154.1143757643.1742926018.1742926018.1742926018.1",
        "__utmc": "81750154",
        "__utmz": "81750154.1742926018.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)",
        "__utmt_UA-11825509-2": "1",
        "__utmb": "81750154.1.10.1742926018",
        "_ga": "GA1.1.562827371.1742926018",
        "_ga_B4734KCGM7": "GS1.1.1742926017.1.0.1742926022.0.0.0",
        "LTSID": "67e2f0c73929971eaac4d4b1",
        "LTAID": "0bc15003-2ffe-41c4-9e7a-eea224fe32ab",
        "lardi_mlogin": "eyJkYXRhIjpbeyJsb2dpbiI6ImRtaXRyb3NpdmlqMSIsImFpZCI6IjBiYzE1MDAzLTJmZmUtNDFjNC05ZTdhLWVlYTIyNGZlMzJhYiIsInRpbWUiOjE3NDI5MjYwMjMxNjIsInJlZklkIjoxMTE3MDM2MTcyMn1dfQ==",
        "lardi_login": "dmitrosivij1",
        "_ga_5M1NYXR1C2": "GS1.1.1742926017.1.0.1742926022.55.0.1652816603",
    }

    url = "https://lardi-trans.com/webapi/proposal/my/search/gruz/published/"
    payload = {"page": 1, "size": 100}
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    response = requests.post(
        url, cookies=cookies, json=payload, headers=headers, timeout=30
    )
    print(response.status_code)
    print(response.text)


if __name__ == "__main__":
    # Используем asyncio.run вместо uc.loop().run_until_complete
    asyncio.run(main())
    get_post()
    # proverka()
