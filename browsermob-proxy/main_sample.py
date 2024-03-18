import requests
import json
import csv
from bs4 import BeautifulSoup
import time
import re
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from browsermobproxy import Server

"""Для прокси нужно jre-8u371-windows-x64.exe т.е. java 8 версии"""
server = Server(r"c:\Program Files (x86)\browsermob-proxy\bin\browsermob-proxy")
server.start()
proxy = server.create_proxy()


def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36')
    # chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--proxy-server={0}".format(proxy.proxy))
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--auto-open-devtools-for-tabs=devtools://devtools/bundled/inspector.html')

    s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=chrome_options)

    return driver


def selenium_get_curl(url):
    proxy.new_har("x-kom", options={'captureHeaders': True, 'captureContent': True})
    """Ссылка куда переходим"""
    driver = get_chromedriver()
    driver.get(url)
    time.sleep(15)
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
        # print(entry)
        """Указываем тут url который нужно отслеживать"""
        if entry['request']['url'].startswith('www.x-kom.pl'):
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
    print(curl_command)
    return curl_command


def get_cookie_header(curl_command):
    cookies = {}  # Инициализация пустым словарем
    headers = {}  # Инициализация пустым словарем

    cookies_match = re.search(r"Cookie:\s(.*?)'", curl_command)
    if cookies_match:
        cookies_str = cookies_match.group(1)
        cookies_list = cookies_str.split('; ')
        cookies = {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookies_list}

    headers_match = re.findall(r"-H '(.*?)'", curl_command)
    headers = {header.split(': ')[0]: header.split(': ')[1] for header in headers_match}

    return cookies, headers


def get_requests(url, cookies, headers):
    response = requests.post(url, cookies=cookies, headers=headers)
    src = response.text
    filename = f"amazon.html"
    with open(filename, "w", encoding='utf-8') as file:
        file.write(src)
    # soup = BeautifulSoup(src, 'lxml')
    # urls = soup.find_all('div', attrs={'class': 'search-result-card__col search-result-card__col_first'})
    # for i in urls:
    #     print(i.find('a').get('href'))
    # json_data = response.json()
    # with open(f'synevo_data.json', 'w', encoding='utf-8') as f:
    #     json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл

if __name__ == '__main__':
    url = "https://www.x-kom.pl/"
    curl_result = selenium_get_curl(url)  # сохраняем результат функции в переменную
    get_cookie_header(curl_result)
    server.stop()  # остановка сервера должна быть здесь
    cookies, headers = get_cookie_header(curl_result)
    get_requests(url, cookies, headers)