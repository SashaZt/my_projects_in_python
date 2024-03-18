import zipfile
import os
import json
import csv
import time
import requests
# Нажатие клавиш
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from selenium import webdriver
import random
from fake_useragent import UserAgent

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

useragent = UserAgent()

# Данные для прокси
PROXY_HOST = '141.145.205.4'
PROXY_PORT = 31281
PROXY_USER = 'proxy_alex'
PROXY_PASS = 'DbrnjhbZ88'

# Настройка для requests чтобы использовать прокси
proxies = {'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}/'}

manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"76.0.0"
}
"""

background_js = """
let config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };
chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}
chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)


def get_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()

    if use_proxy:
        plugin_file = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr('manifest.json', manifest_json)
            zp.writestr('background.js', background_js)

        chrome_options.add_extension(plugin_file)

    if user_agent:
        chrome_options.add_argument(f'--user-agent={user_agent}')

    s = Service(
        executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    )

    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )

    return driver


def main(url):
    driver = get_chromedriver(use_proxy=True,
                              user_agent=f"{useragent.random}")
    driver.get(url)
    e_mail = 'a.zinchyk83@gmail.com'
    pas_s = 'RqgP9jXkND!xTDP'
    driver.get(url=url)
    driver.maximize_window()
    time.sleep(5)
    try:
        log_in = driver.find_element(By.XPATH, '//span[text() = "Log In"]').click()
    except:
        log_in = print('No Log In')
    time.sleep(10)
    try:
        button_email = driver.find_element(By.XPATH, '//input[@autocomplete="email"]')
        button_email.send_keys(e_mail)
        time.sleep(5)
    except:
        button_email = print('Not email')
    try:
        button_pass = driver.find_element(By.XPATH, '//input[@autocomplete="current-password"]')
        button_pass.send_keys(pas_s)
        time.sleep(5)
    except:
        button_pass = print('Not pass')

    try:
        button_in = driver.find_element(By.XPATH,
                                        '//button[@class="mat-focus-indicator login mat-raised-button mat-button-base mat-primary mat-button-disabled"]').click()
    except:
        button_in = print('Not in')
    driver.close()
    driver.quit()


if __name__ == '__main__':
    url = "https://www.crunchbase.com"
    main(url)
