# -*- coding: utf-8 -*-
import glob
import json
import os
import random
from datetime import datetime

import gspread
import mysql.connector
from oauth2client.service_account import ServiceAccountCredentials
from config import db_config, database, spreadsheet_id, use_table_chat, db_config_asio
from proxi import proxies

current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
cookies_path = os.path.join(temp_path, 'cookies')
login_pass_path = os.path.join(temp_path, 'login_pass')
daily_sales_path = os.path.join(temp_path, 'daily_sales')
monthly_sales_path = os.path.join(temp_path, 'monthly_sales')
payout_history_path = os.path.join(temp_path, 'payout_history')
pending_custom_path = os.path.join(temp_path, 'pending_custom')
chat_path = os.path.join(temp_path, 'chat')
max_attempts = 3
attempts = 0


def log_message(message, log_filename="log.txt"):
    """
    Функция для логирования сообщений в файл.

    :param message: Сообщение для логирования.
    :param log_filename: Имя файла лога.
    """
    with open(log_filename, 'a', encoding='utf-8') as log_file:
        log_file.write(message + '\n')


def proxy_random():
    """
    Функция для случайного прокси
    """
    proxy = random.choice(proxies)
    proxy_host = proxy[0]
    proxy_port = proxy[1]
    proxy_user = proxy[2]
    proxy_pass = proxy[3]
    formatted_proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"

    # Возвращаем словарь с прокси
    return {"http": formatted_proxy, "https": formatted_proxy}


def delete_all_files():
    """
    Функция для удаления временных файлов по всем папкам
    """
    all_path = [chat_path, daily_sales_path, payout_history_path, pending_custom_path]

    for path in all_path:
        # Получаем список всех файлов в директории
        files = glob.glob(os.path.join(path, '*'))
        for f in files:
            # Проверяем, является ли путь файлом
            if os.path.isfile(f):
                os.remove(f)  # Удаляем файл
            elif os.path.isdir(f):
                # Если нужно удалить и поддиректории, раскомментируйте следующие строки
                # for subfile in glob.glob(os.path.join(f, '*')):
                #     os.remove(subfile)  # Удаляем файлы в поддиректории
                # os.rmdir(f)  # Удаляем саму поддиректорию
                print(f"Directory {f} skipped.")


def get_google():
    """
    Функция для подключения к Google sheets
    """
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
    creds_file = os.path.join(current_directory, 'access.json')
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    return client, spreadsheet_id


def get_id_models_from_sql():
    """
    Функция для получения данных с Mysql
    """
    # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    # Выполнение запроса для получения уникальных значений
    cursor.execute(f"SELECT DISTINCT model_fm, model_id FROM {database}.daily_sales")

    dict_models = {}
    # Получение и вывод результатов
    results = cursor.fetchall()
    for row in results:
        model_id, mvtoken = row
        dict_models[model_id] = mvtoken
    # Закрытие курсора и соединения
    cursor.close()
    cnx.close()
    return dict_models


def get_latest_chat_date():
    """
    Функция для получения последней даты чата с Mysql
    """
    sql_data = check_chat()
    if sql_data:
        latest_date_tuple = max(sql_data, key=lambda x: datetime.strptime(x[1], '%Y-%m-%d %H:%M:%S'))
        latest_date = latest_date_tuple[1]  # Извлекаем дату из кортежа
    else:
        # Если sql_data пуст, устанавливаем latest_date в None или другое значение по умолчанию
        # Это значение можно использовать для проверки необходимости выполнения следующих шагов
        latest_date = None
        log_message("Нет данных для обработки. Продолжаем выполнение скрипта.")
    log_message(f'Последняя дата в БД {latest_date}')
    return latest_date


def get_cookies():
    """
    Функция для работы с cookies
    """
    filename_cookies = os.path.join(current_directory, 'cookies.json')
    with open(filename_cookies, 'r', encoding="utf-8") as f:
        data_json = json.load(f)
    questionnaires_json = data_json['questionnaires']
    models_cookies = []

    for s in questionnaires_json:
        # Собираем информацию о каждом магазине
        model_info = {"model": s['model'], "mvtoken": s['mvtoken'], "cookies": s['cookies']}
        # Добавляем информацию о магазине в список
        models_cookies.append(model_info)

    # Возвращаем список с информацией о всех магазинах и их cookies
    return models_cookies


def check_chat():
    """
    Функция для получение из БД чатов
    """
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    cursor.execute(f"""
        SELECT msg_last_id, CONCAT(date_part, ' ', time_part) AS datetime FROM {database}.chat;
    """)
    data = {(row[0], row[1]) for row in cursor.fetchall()}
    cursor.close()
    cnx.close()
    return data


def get_sql_chat():
    """
    Функция для отправки данных об чатах в Mysql
    """
    sql_data = check_chat()
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    latest_date = get_latest_chat_date()
    folder = os.path.join(chat_path, '*.json')
    files_json = glob.glob(folder)
    models_fms = get_id_models_from_sql()

    for item in files_json:
        with open(item, 'r', encoding="utf-8") as f:
            raw_json_str = f.read()
            data_json = json.loads(raw_json_str)
            data_json = json.loads(data_json)
        try:
            json_data = data_json['conversations']
        except:
            json_data = None
            continue
        for dj in json_data['list']:
            msg_last_id = dj['msg_last_id']  # id чата
            sender_id = dj['sender_id']  # id  модели
            user_id = dj['user_id']  # id  клиента
            msg_date = dj['msg_date']  # дата  чата
            msg_date = datetime.strptime(msg_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            # log_message(f'в Чате {msg_date} последняя дата {latest_date}')

            if msg_date == latest_date:
                should_stop = True  # Устанавливаем флаг в True, когда нашли совпадение
                log_message('Стоп')
                break  # Прерываем внутренний цикл
            date_part, time_part = msg_date.split(' ')
            json_data_chat = (msg_last_id, msg_date)
            values = [msg_last_id, user_id, sender_id, date_part, time_part]

            if not json_data_chat in sql_data:
                # SQL-запрос для вставки данных
                insert_query = f"""
                                                INSERT IGNORE INTO {use_table_chat}
                                                (msg_last_id, user_id, sender_id, date_part, time_part)
                                                VALUES (%s, %s, %s, %s, %s)
                                                """
                cursor.execute(insert_query, values)

                cnx.commit()  # Подтверждение изменений
            else:
                break


def get_asio():
    import glob
    import asyncio
    import json
    import os
    import random
    from datetime import datetime

    import aiofiles
    import aiohttp
    import aiomysql
    from aiohttp import BasicAuth
    from playwright.async_api import TimeoutError
    from playwright.async_api import async_playwright

    from config import db_config_asio, headers
    from proxi import proxies

    current_directory = os.getcwd()
    temp_directory = 'temp'
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, temp_directory)
    cookies_path = os.path.join(temp_path, 'cookies')
    daily_sales_path = os.path.join(temp_path, 'daily_sales')
    payout_history_path = os.path.join(temp_path, 'payout_history')
    pending_custom_path = os.path.join(temp_path, 'pending_custom')
    chat_path = os.path.join(temp_path, 'chat')

    async def proxy_random():
        proxy = random.choice(proxies)
        proxy_host = proxy[0]
        proxy_port = proxy[1]
        proxy_user = proxy[2]
        proxy_pass = proxy[3]

        # Возвращаем словарь, соответствующий ожидаемому формату для Playwright
        return {
            'server': f'http://{proxy_host}:{proxy_port}',
            'username': proxy_user,
            'password': proxy_pass,
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
            data_dict = {'identifier': record[0], 'login': record[1], 'password': record[2]}
            data_list.append(data_dict)

        await cursor.close()
        conn.close()
        return data_list

    async def update_session_cookies(session, cookies):
        for cookie in cookies:
            session.cookie_jar.update_cookies({cookie['name']: cookie['value']})

    async def save_cookies(page, identifier, mvtoken):
        cookies = await page.context.cookies()
        # Убедитесь, что mvtoken корректен и не является объектом корутины
        filename = os.path.join(cookies_path, f"{identifier}_{mvtoken}.json")
        async with aiofiles.open(filename, 'w') as f:
            await f.write(json.dumps(cookies))
        # print(f"Сохранены куки для {identifier}")
        return filename

    async def load_cookies_and_update_session(session, filename):
        async with aiofiles.open(filename, 'r') as f:
            cookies_list = json.loads(await f.read())
        for cookie in cookies_list:
            session.cookie_jar.update_cookies({cookie['name']: cookie['value']})

    async def get_requests_day(session, proxy, headers, mvtoken, month, filterYear, filename):
        data = {'mvtoken': mvtoken,
                'day': '',
                'month': month,
                'filterYear': filterYear
                }
        """Получаем дневные продажи"""
        # Загрузка кук из файла и обновление сессии
        await load_cookies_and_update_session(session, filename)

        roxy_auth = None
        if proxy['username'] and proxy['password']:
            proxy_auth = BasicAuth(login=proxy['username'], password=proxy['password'])

        async with session.post('https://www.manyvids.com/includes/get_earnings.php',
                                headers=headers, proxy=proxy['server'],
                                proxy_auth=proxy_auth, data=data) as response:
            data_json = await response.text()
            return data_json
            # if response.headers.get('Content-Type') == 'application/json':
            #     data_json = await response.json()
            #     return data_json
            # else:
            #     content = await response.text()
            #     print(f'Unexpected response: {content}')
            #     return None

    async def get_requests_chat(session, proxy, headers, mvtoken, filename):
        data = {
            'mvtoken': mvtoken,
            'typeMessage': 'private',
            'action': 'clc',
            'isMobile': '0'
        }
        """Получаем дневные продажи"""
        # Загрузка кук из файла и обновление сессии
        await load_cookies_and_update_session(session, filename)

        roxy_auth = None
        if proxy['username'] and proxy['password']:
            proxy_auth = BasicAuth(login=proxy['username'], password=proxy['password'])

        async with session.post('https://www.manyvids.com/includes/user_messages.php',
                                headers=headers, proxy=proxy['server'],
                                proxy_auth=proxy_auth, data=data) as response:
            data_json = await response.text()
            return data_json

    async def save_chat_json(data_json, mvtoken):
        filename = os.path.join(chat_path, f'{mvtoken}.json')
        async with aiofiles.open(filename, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(data_json, ensure_ascii=False, indent=4))

    async def get_total_msg():
        folder = os.path.join(chat_path, '*.json')
        files_json = glob.glob(folder)
        total_pages = 0

        for item in files_json:
            filename = os.path.basename(item)
            parts = filename.split("_")
            mvtoken_cookies = parts[0]

            async with aiofiles.open(item, 'r', encoding="utf-8") as f:
                json_data = await f.read()
                json_string_unescaped = json.loads(json_data)

                # Второе преобразование: из строки JSON в объект Python (в данном случае, в словарь)
                json_data = json.loads(json_string_unescaped)
                # json_data = json.loads(json_data)

                data_json = json_data['conversations']
                total_msg = int(data_json['meta']['total'])
                total_pages += (total_msg // 13) + 2

        return total_pages

    async def get_requests_all_chat(session, proxy, headers, mvtoken, filename, total_msg):
        offset = 0
        results = []  # Собираем результаты здесь

        for i in range(1, total_msg):  # Исправлено на range
            await load_cookies_and_update_session(session, filename)

            proxy_auth = None
            if proxy['username'] and proxy['password']:
                proxy_auth = BasicAuth(login=proxy['username'], password=proxy['password'])

            # Подготовка данных запроса
            data = {
                'mvtoken': mvtoken,
                'typeMessage': 'private',
                'action': 'clc' if i == 1 else 'cl',
                'isMobile': '0'
            }
            if i > 1:
                offset += 13
                data.update({'offset': offset, 'type': 'all'})

            # Выполнение запроса
            async with session.post('https://www.manyvids.com/includes/user_messages.php',
                                    headers=headers, proxy=proxy['server'],
                                    proxy_auth=proxy_auth, data=data) as response:
                data_json = await response.text()
                results.append((data_json, i))  # Добавляем результат в список
                # Добавляем случайную задержку от 0 до 5 секунд
            await asyncio.sleep(random.uniform(0, 5))
            if i == 200:  # Прерываем цикл после обработки пяти итераций
                break

        return results  # Возвращаем собранные результаты после завершения цикла

    async def save_all_chat_json(data_json, mvtoken, i):
        filename = os.path.join(chat_path, f'{mvtoken}_{i}.json')
        async with aiofiles.open(filename, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(data_json, ensure_ascii=False, indent=4))

    async def run(playwright):
        now = datetime.now()
        month = str(now.month)
        filterYear = str(now.year)
        proxy = await proxy_random()
        data_login_pass = await login_pass()
        for item in data_login_pass:
            # """Список логинов у которых не правильные пароли"""
            # skip_logins = [
            #    'MaryRo',
            #    'Real Sasha Grey',
            # ]
            #
            # if item['login'] in skip_logins:
            #    continue
            async with aiohttp.ClientSession() as session:

                browser = await playwright.chromium.launch(headless=False, proxy=proxy)
                context = await browser.new_context()
                page = await context.new_page()
                """Вход на страницу с логин и пароль"""
                try:
                    await page.goto('https://www.manyvids.com/Login/', wait_until='networkidle',
                                    timeout=60000)  # 60 секунд
                    # await page.goto('https://www.manyvids.com/Login/', wait_until='load', timeout=60000) нужно тестировать
                except TimeoutError:
                    print(f"Страница не загрузилась для {item['login']} 60 секунд.")
                    continue
                try:
                    # Ожидаем появления элемента h1 с текстом "Login to ManyVids"
                    await page.wait_for_selector('h1:text("Login to ManyVids")', timeout=60000)
                    await page.fill('input#triggerUsername', item['login'])
                    await page.fill('input#triggerPassword', item['password'])
                except TimeoutError:
                    print(f"Страница не загрузилась для {item['login']} 60 секунд.")
                    continue

                # Попытка входа и повтор в случае необходимости
                max_attempts = 3  # Максимальное количество попыток
                attempts = 0  # Счетчик попыток

                """Проверяем или кнопка login  пропала"""
                while attempts < max_attempts:
                    await page.press('input#triggerPassword', 'Enter')
                    try:
                        # Ожидаем исчезновение элемента reCAPTCHA в течение определенного времени
                        await page.wait_for_selector('//a[@data-recaptcha-action="login"]', state='hidden',
                                                     timeout=10000)
                        print(f"Успешный вход {item['login']}")
                        break  # Если элемент исчез, выходим из цикла
                    except TimeoutError:
                        # Если элемент не исчез в течение заданного времени, увеличиваем счетчик попыток и пытаемся снова
                        print(f"Попытка {attempts + 1} из {max_attempts} не удалась")
                        attempts += 1
                        if attempts < max_attempts:
                            await asyncio.sleep(10)  # Ждем перед следующей попыткой

                if attempts >= max_attempts:
                    print(f"Проверьте логин и пароль {item['login']}")

                """Переход на страницу с данными"""
                try:
                    await page.goto('https://www.manyvids.com/View-my-earnings/', wait_until='networkidle',
                                    timeout=60000)  # 60 секунд
                    # await page.goto('https://www.manyvids.com/Login/', wait_until='load', timeout=60000) нужно тестировать
                except TimeoutError:
                    print(f"Страница не загрузилась для {item['login']} 60 секунд.")
                    continue
                try:
                    # Ожидаем элемент в течение 30 секунд
                    element = await page.wait_for_selector('//div[@class="text-left"]', timeout=60000)
                    # Если элемент найден, останавливаем загрузку страницы
                    # if element:
                    #     await page.evaluate("window.stop()")
                except TimeoutError:
                    print(f"Страница не загрузилась для {item['login']} 60 секунд.")
                    continue

                await page.wait_for_selector('[data-mvtoken]')
                mvtoken = await page.get_attribute('[data-mvtoken]', 'data-mvtoken')  # Используйте await здесь
                filename = await save_cookies(page, item['identifier'], mvtoken)

                await load_cookies_and_update_session(session, filename)  # Загружаем куки в session

                """Загрузка чатов"""
                data_json_first_chat = await get_requests_chat(session, proxy, headers, mvtoken, filename)
                #
                await save_chat_json(data_json_first_chat, mvtoken)

                total_msg = await get_total_msg()
                # data_json_all_chat, i = await get_requests_all_chat(session, proxy, headers, mvtoken, filename, total_msg)

                results = await get_requests_all_chat(session, proxy, headers, mvtoken, filename, total_msg)
                for data_json, i in results:
                    await save_all_chat_json(data_json, mvtoken, i)

                # latest_date = await check_chat()

                """Закрываем"""
                await browser.close()

    async def main():
        async with async_playwright() as playwright:
            await run(playwright)

    asyncio.run(main())


if __name__ == '__main__':
    get_asio()
    get_sql_chat()
