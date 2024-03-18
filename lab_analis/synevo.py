import csv
import json
import os
import re
import time

import requests
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

"""Для прокси нужно jre-8u371-windows-x64.exe т.е. java 8 версии"""
server = Server(r"c:\Program Files (x86)\browsermob-proxy\bin\browsermob-proxy")
server.start()
proxy = server.create_proxy()


def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--proxy-server={0}".format(proxy.proxy))
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--auto-open-devtools-for-tabs=devtools://devtools/bundled/inspector.html')

    current_directory = os.getcwd()
    folder = f'{current_directory}\chromedriver.exe'
    s = Service(executable_path=folder)
    driver = webdriver.Chrome(service=s, options=chrome_options)

    return driver


def selenium_get_curl():
    proxy.new_har("synevo", options={'captureHeaders': True, 'captureContent': True})

    url = "https://www.synevo.ua/ua/tests"
    driver = get_chromedriver()
    driver.get(url)
    time.sleep(5)
    driver.execute_script('''
        var elements = document.querySelectorAll('[aria-label="Network panel"]');
        for (var i = 0; i < elements.length; i++) {
            var element = elements[i];
            if (element.offsetWidth > 0 && element.offsetHeight > 0) {
                element.click();
                break;
            }
        }
    ''')
    time.sleep(5)
    # получить все запросы из Network panel
    requests = driver.execute_script('''
        var performanceEntries = performance.getEntriesByType("resource");
        var fetchRequests = [];
        for (var i = 0; i < performanceEntries.length; i++) {
            var entry = performanceEntries[i];
            fetchRequests.push(entry);
        }
        return fetchRequests;
    ''')

    curl_command = "curl "
    entries = proxy.har['log']['entries']
    for entry in entries:
        """Указываем тут url который нужно отслеживать"""
        if entry['request']['url'] == 'https://www.synevo.ua/api/test/tests-by-loc':
            # Method (GET, POST, etc.)
            curl_command += "-X {} ".format(entry['request']['method'])

            # URL
            curl_command += "'{}' \\\n".format(entry['request']['url'])

            # Headers
            for header in entry['request']['headers']:
                header_name = header['name']
                header_value = header['value']
                curl_command += "  -H '{}: {}' \\\n".format(header_name, header_value)

            if entry['request']['method'] == 'POST' and 'postData' in entry['request']:
                if 'text' in entry['request']['postData']:
                    curl_command += "  --data '{}'".format(entry['request']['postData']['text'])

            break
    # Extracting cookies
    cookies_match = re.search(r"Cookie:\s(.*?)'", curl_command)
    if cookies_match:
        cookies_str = cookies_match.group(1)
        cookies_list = cookies_str.split('; ')
        cookies = {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookies_list}

    # Extracting headers
    headers_match = re.findall(r"-H '(.*?)'", curl_command)
    headers = {header.split(': ')[0]: header.split(': ')[1] for header in headers_match}

    return curl_command


def get_cookie_header(curl_command):
    cookies_match = re.search(r"Cookie:\s(.*?)'", curl_command)
    cookies = {}
    if cookies_match:
        cookies_str = cookies_match.group(1)
        cookies_list = cookies_str.split('; ')
        cookies = {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookies_list}

    # Extracting headers
    headers_match = re.findall(r"-H '(.*?)'", curl_command)
    headers = {header.split(': ')[0]: header.split(': ')[1] for header in headers_match}
    return cookies, headers


def get_synevo(cookies, headers):
    data = {
        'location_id': '26',
    }

    response = requests.post('https://www.synevo.ua/api/test/tests-by-loc', cookies=cookies, headers=headers, data=data)
    json_data = response.json()
    with open(f'synevo_data.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл


def parsing_synevo():
    file_name = 'synevo_data.json'
    with open(file_name, encoding='utf-8') as f:
        data = json.load(f)
    heandler = ['code', 'name_ru', 'name_ua', 'term', 'location_id', 'price']
    with open('synevo.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(heandler)  # Записываем заголовки только один раз
        for key in data['json']:
            for item in data['json'][key]:
                code = item['code']
                name_ru = item['name_ru']
                name_ua = item['name_ua']
                term = item['term']
                location_id = item['location_id']
                price = item['price']
                values = [code, name_ru, name_ua, term, location_id, price]
                writer.writerow(values)


if __name__ == '__main__':
    curl_result = selenium_get_curl()  # сохраняем результат функции в переменную
    get_cookie_header(curl_result)
    server.stop()  # остановка сервера должна быть здесь
    cookies, headers = get_cookie_header(curl_result)
    get_synevo(cookies, headers)
    parsing_synevo()
