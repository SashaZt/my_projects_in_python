def get_asio():
    import glob
    import asyncio
    import json
    import os
    import random
    from datetime import datetime
    from asyncio import create_task, wait, FIRST_COMPLETED

    import aiofiles
    import aiohttp
    import aiomysql
    from aiohttp import BasicAuth
    from playwright.async_api import TimeoutError
    from playwright.async_api import async_playwright

    from config import db_config_asio, headers, use_bd
    from proxi import proxies

    current_directory = os.getcwd()
    temp_directory = "temp"
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, temp_directory)
    cookies_path = os.path.join(temp_path, "cookies")
    daily_sales_path = os.path.join(temp_path, "daily_sales")
    payout_history_path = os.path.join(temp_path, "payout_history")
    pending_custom_path = os.path.join(temp_path, "pending_custom")
    chat_path = os.path.join(temp_path, "chat")

    async def proxy_random():
        proxy = random.choice(proxies)
        proxy_host = proxy[0]
        proxy_port = proxy[1]
        proxy_user = proxy[2]
        proxy_pass = proxy[3]

        # Возвращаем словарь, соответствующий ожидаемому формату для Playwright
        return {
            "server": f"http://{proxy_host}:{proxy_port}",
            "username": proxy_user,
            "password": proxy_pass,
        }

    async def login_pass():
        # Список для хранения данных
        data_list = []

        # Устанавливаем соединение с базой данных
        conn = await aiomysql.connect(**db_config_asio)
        cursor = await conn.cursor()

        await cursor.execute("SELECT identifier, login, pass FROM login_pass;")

        # Получение всех записей
        records = await cursor.fetchall()

        for record in records:
            # Создание словаря для каждой строки и добавление его в список
            data_dict = {
                "identifier": record[0],
                "login": record[1],
                "password": record[2],
            }
            data_list.append(data_dict)

        await cursor.close()
        conn.close()
        return data_list

    async def update_session_cookies(session, cookies):
        for cookie in cookies:
            session.cookie_jar.update_cookies({cookie["name"]: cookie["value"]})

    async def save_cookies(page, identifier, mvtoken):
        cookies = await page.context.cookies()
        # Убедитесь, что mvtoken корректен и не является объектом корутины
        filename = os.path.join(cookies_path, f"{identifier}_{mvtoken}.json")
        async with aiofiles.open(filename, "w") as f:
            await f.write(json.dumps(cookies))
        # print(f"Сохранены куки для {identifier}")
        return filename

    async def load_cookies_and_update_session(session, filename):
        async with aiofiles.open(filename, "r") as f:
            cookies_list = json.loads(await f.read())
        for cookie in cookies_list:
            session.cookie_jar.update_cookies({cookie["name"]: cookie["value"]})

    async def get_requests_day(
        session, proxy, headers, mvtoken, month, filterYear, filename
    ):
        data = {"mvtoken": mvtoken, "day": "", "month": month, "filterYear": filterYear}
        """Получаем дневные продажи"""
        # Загрузка кук из файла и обновление сессии
        await load_cookies_and_update_session(session, filename)

        roxy_auth = None
        if proxy["username"] and proxy["password"]:
            proxy_auth = BasicAuth(login=proxy["username"], password=proxy["password"])

        async with session.post(
            "https://www.manyvids.com/includes/get_earnings.php",
            headers=headers,
            proxy=proxy["server"],
            proxy_auth=proxy_auth,
            data=data,
        ) as response:
            data_json = await response.text()
            return data_json

    async def save_day_json(data_json, mvtoken, month, filterYear):
        filename = os.path.join(
            daily_sales_path, f"{mvtoken}_{month}_{filterYear}.json"
        )
        async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(data_json, ensure_ascii=False, indent=4))

    async def get_requests_history(
        session, proxy, headers, mvtoken, filterYear, filename
    ):
        data = {"mvtoken": mvtoken, "year": filterYear}
        """Получаем дневные продажи"""
        # Загрузка кук из файла и обновление сессии
        await load_cookies_and_update_session(session, filename)

        roxy_auth = None
        if proxy["username"] and proxy["password"]:
            proxy_auth = BasicAuth(login=proxy["username"], password=proxy["password"])

        async with session.post(
            "https://www.manyvids.com/includes/get_payperiod_earnings.php",
            headers=headers,
            proxy=proxy["server"],
            proxy_auth=proxy_auth,
            data=data,
        ) as response:
            data_json = await response.text()
            return data_json

    async def save_history_json(data_json, mvtoken, filterYear):
        filename = os.path.join(payout_history_path, f"{mvtoken}_{filterYear}.json")
        async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(data_json, ensure_ascii=False, indent=4))

    async def save_page_content(page, mvtoken, filterYear):
        filename = os.path.join(pending_custom_path, f"{mvtoken}_{filterYear}.html")
        content = await page.content()
        async with aiofiles.open(filename, "w", encoding="utf-8") as f:
            await f.write(content)

    async def get_requests_chat(session, proxy, headers, mvtoken, filename):
        data = {
            "mvtoken": mvtoken,
            "typeMessage": "private",
            "action": "clc",
            "isMobile": "0",
        }
        """Получаем дневные продажи"""
        # Загрузка кук из файла и обновление сессии
        await load_cookies_and_update_session(session, filename)

        roxy_auth = None
        if proxy["username"] and proxy["password"]:
            proxy_auth = BasicAuth(login=proxy["username"], password=proxy["password"])

        async with session.post(
            "https://www.manyvids.com/includes/user_messages.php",
            headers=headers,
            proxy=proxy["server"],
            proxy_auth=proxy_auth,
            data=data,
        ) as response:
            data_json = await response.text()
            return data_json

    async def save_chat_json(data_json, mvtoken):
        filename = os.path.join(chat_path, f"{mvtoken}.json")
        async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(data_json, ensure_ascii=False, indent=4))

    async def get_total_msg():
        folder = os.path.join(chat_path, "*.json")
        files_json = glob.glob(folder)
        total_pages = 0

        for item in files_json:
            filename = os.path.basename(item)
            parts = filename.split("_")
            mvtoken_cookies = parts[0]

            async with aiofiles.open(item, "r", encoding="utf-8") as f:
                json_data = await f.read()
                json_string_unescaped = json.loads(json_data)

                # Второе преобразование: из строки JSON в объект Python (в данном случае, в словарь)
                json_data = json.loads(json_string_unescaped)
                # json_data = json.loads(json_data)

                data_json = json_data["conversations"]
                total_msg = int(data_json["meta"]["total"])
                total_pages += (total_msg // 13) + 2

        return total_pages

    async def get_requests_all_chat(
        session, proxy, headers, mvtoken, filename, total_msg
    ):
        offset = 0
        results = []  # Собираем результаты здесь

        for i in range(1, total_msg):  # Исправлено на range
            await load_cookies_and_update_session(session, filename)

            proxy_auth = None
            if proxy["username"] and proxy["password"]:
                proxy_auth = BasicAuth(
                    login=proxy["username"], password=proxy["password"]
                )

            # Подготовка данных запроса
            data = {
                "mvtoken": mvtoken,
                "typeMessage": "private",
                "action": "clc" if i == 1 else "cl",
                "isMobile": "0",
                "type": "all",
            }
            if i > 1:
                offset += 13
                data.update({"offset": offset})

            # Выполнение запроса
            async with session.post(
                "https://www.manyvids.com/includes/user_messages.php",
                headers=headers,
                proxy=proxy["server"],
                proxy_auth=proxy_auth,
                data=data,
            ) as response:
                data_json = await response.text()
                results.append((data_json, i))  # Добавляем результат в список
                # Добавляем случайную задержку от 0 до 5 секунд
            await asyncio.sleep(random.uniform(0, 2))
            if i == 5:  # Прерываем цикл после обработки пяти итераций
                break

        return results  # Возвращаем собранные результаты после завершения цикла

    async def save_all_chat_json(data_json, mvtoken, i):
        filename = os.path.join(chat_path, f"{mvtoken}_{i}.json")
        async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(data_json, ensure_ascii=False, indent=4))

    async def run(playwright):
        # Попытка входа и повтор в случае необходимости
        max_attempts = 5  # Максимальное количество попыток
        attempts = 0  # Счетчик попыток
        now = datetime.now()
        month = str(now.month)
        filterYear = str(now.year)

        data_login_pass = await login_pass()
        timeout_ancet = 100000
        async with aiohttp.ClientSession() as session:
            for item in data_login_pass[:1]:
                successful_login = False

                attempts = 0
                while attempts < max_attempts and not successful_login:
                    proxy = (
                        await proxy_random()
                    )  # Получение нового прокси при каждой попытке
                    browser = await playwright.chromium.launch(
                        headless=False, proxy=proxy
                    )
                    context = await browser.new_context()
                    page = await context.new_page()

                    try:

                        await page.goto(
                            "https://www.manyvids.com/Login/",
                            wait_until="load",
                            timeout=timeout_ancet,
                        )
                        # await asyncio.sleep(60)
                        # Ожидаем появления заголовка с текстом "Sign in to ManyVids" на странице
                        await page.wait_for_selector(
                            'text="Sign in to ManyVids"', timeout=timeout_ancet
                        )

                        # Заполнение поля ввода имени пользователя, после того как оно появится
                        await page.wait_for_selector(
                            "input[name='userName']", timeout=timeout_ancet
                        )
                        await page.fill("input[name='userName']", item["login"])

                        # Заполнение поля ввода пароля, после того как оно появится
                        await page.wait_for_selector(
                            "input[name='password'][type='password']",
                            timeout=timeout_ancet,
                        )
                        await page.fill("input[name='password']", item["password"])

                        await page.press("input[name='password']", "Enter")
                        await asyncio.sleep(10)

                        login_task = page.wait_for_selector(
                            "button:has-text('Sign In')",
                            state="attached",  # Используем 'attached' для проверки, что кнопка присутствует на странице
                            timeout=1000,
                        )
                        error_task = page.wait_for_selector(
                            "span[class*='Snackbar_message']", timeout=1000
                        )

                        results = await asyncio.gather(
                            login_task,
                            error_task,
                            return_exceptions=True,
                        )

                        if isinstance(results[1], Exception):
                            # print(f"Успешный вход для {item['login']}")
                            successful_login = True
                        else:
                            error_text = await results[1].text_content()
                            print(f'{item["login"]}: {error_text}')

                            if (
                                "Check Username & Password are correct and re-try"
                                in error_text
                            ):
                                attempts += 5  # Если сообщение об ошибке указывает на проблему с учетными данными, увеличиваем попытки
                            else:
                                attempts += 1  # Для других ошибок увеличиваем на 1

                            await browser.close()  # Закрываем браузер после обработки ошибки

                    except Exception as e:
                        print(
                            f"Ошибка при попытке входа для {item['login']} на попытке {attempts + 1}: {str(e)}"
                        )
                        attempts += 1
                        await browser.close()  # Закрыть браузер при ошибке

                if successful_login:
                    # Продолжаем использовать текущий браузер и прокси
                    try:
                        await asyncio.sleep(5)
                        await page.goto(
                            "https://www.manyvids.com/View-my-earnings/",
                            wait_until="load",
                            timeout=timeout_ancet,
                        )
                        try:
                            await page.wait_for_selector(
                                '//div[@class="text-left"]', timeout=timeout_ancet
                            )
                        except:
                            print(
                                f"Страница не загрузилась для {item['login']} 60 секунд."
                            )
                            await browser.close()

                        await page.wait_for_selector(
                            "[data-mvtoken]", timeout=timeout_ancet
                        )
                        mvtoken = await page.get_attribute(
                            "[data-mvtoken]", "data-mvtoken"
                        )
                        filename = await save_cookies(page, item["identifier"], mvtoken)

                        await load_cookies_and_update_session(session, filename)

                        """Дневные продажи"""
                        data_json_day = await get_requests_day(
                            session,
                            proxy,
                            headers,
                            mvtoken,
                            month,
                            filterYear,
                            filename,
                        )
                        await save_day_json(data_json_day, mvtoken, month, filterYear)

                        """История"""
                        data_json_history = await get_requests_history(
                            session, proxy, headers, mvtoken, filterYear, filename
                        )
                        await save_history_json(data_json_history, mvtoken, filterYear)

                        """Pending"""
                        await save_page_content(page, mvtoken, filterYear)
                        #

                        """Загрузка чатов"""
                        data_json_first_chat = await get_requests_chat(
                            session, proxy, headers, mvtoken, filename
                        )
                        #
                        await save_chat_json(data_json_first_chat, mvtoken)

                        total_msg = await get_total_msg()

                        results = await get_requests_all_chat(
                            session, proxy, headers, mvtoken, filename, total_msg
                        )
                        for data_json, i in results:
                            await save_all_chat_json(data_json, mvtoken, i)

                    except Exception as e:
                        print(
                            f"Не удалось загрузить страницу заработков для {item['login']}: {str(e)}"
                        )
                    finally:
                        await browser.close()
                else:
                    print(
                        f"Не удалось войти для {item['login']} после {max_attempts} попыток."
                    )

                """Закрываем"""
            await browser.close()

    async def main():
        async with async_playwright() as playwright:
            await run(playwright)

    asyncio.run(main())
