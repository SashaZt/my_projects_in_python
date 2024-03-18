import glob
import json
import os
import random
import time

import mysql.connector
from playwright.sync_api import sync_playwright

from config import db_config
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


def save_cookies(page):
    return page.context.cookies()


def creative_folders():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, cookies_path, login_pass_path, daily_sales_path, monthly_sales_path, payout_history_path,
                   pending_custom_path, chat_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)



def proxy_random():
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


def login_pass():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute("""
        SELECT identifier, login, pass FROM manyvids.login_pass;
    """)

    # Получение всех записей
    records = cursor.fetchall()

    # Список для хранения данных
    data_list = []

    for record in records:
        # Создание словаря для каждой строки и добавление его в список
        data_dict = {'identifier': record[0], 'login': record[1], 'password': record[2]}
        data_list.append(data_dict)

    cursor.close()
    cnx.close()
    return data_list


def run(playwright):
    folders = creative_folders()
    proxy = proxy_random()
    data_login_pass = login_pass()
    # Получаем список всех файлов в папке
    files = glob.glob(os.path.join(cookies_path, '*'))
    # Удаляем каждый файл
    for f in files:
        if os.path.isfile(f):
            os.remove(f)
    for item in data_login_pass:
        # if not os.path.exists(filename_coockies):  # Проверка на существование файла
        login = item['login']
        password = item['password']

        # """Так передаем один прокси для playwright"""
        # browser = playwright.chromium.launch(headless=False, proxy={
        #     'server': 'http://85.237.196.5:51523',  # Замените на ваш прокси-сервер
        #     'username': 'locomgmt',  # Имя пользователя прокси
        #     'password': 'ogzj4wAZnz'  # Пароль прокси
        # })

        # """Так передаем случайные прокси для playwright"""
        browser = playwright.chromium.launch(headless=False, proxy=proxy)

        context = browser.new_context()
        page = context.new_page()
        page.goto('https://www.manyvids.com/Login/')
        # Находим элемент ввода логина и вводим значение
        page.fill('input#triggerUsername', login)
        #
        # # Находим элемент ввода пароля и вводим значение
        page.fill('input#triggerPassword', password)

        # Нажимаем Enter после ввода пароля
        page.press('input#triggerPassword', 'Enter')
        # Здесь добавьте действия для входа на сайт: ввод логина, пароля и нажатие на кнопку входа.

        time.sleep(10)
        page.goto('https://www.manyvids.com/View-my-earnings/')

        time.sleep(10)
        page.wait_for_selector('[data-mvtoken]')
        mvtoken = page.get_attribute('[data-mvtoken]', 'data-mvtoken')
        filename_coockies = os.path.join(cookies_path, f"{item['identifier']}_{mvtoken}.json")
        cookies = save_cookies(page)
        # Сохранение кук в файл
        cookies = context.cookies()
        with open(filename_coockies, 'w') as f:
            json.dump(cookies, f)
        print(f"Сохрани {item['identifier']}")
        browser.close()
        browser.close()


with sync_playwright() as playwright:
    run(playwright)
