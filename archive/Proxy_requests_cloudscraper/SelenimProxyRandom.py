# Нажатие клавиш
import csv
import time
from selenium import webdriver
# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.chrome.service import Service
# Нажатие клавиш
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from selenium import webdriver

useragent = UserAgent()
from selenium.webdriver.chrome.service import Service

proxy_list = []
with open('proxylist.csv', 'r') as files:
    reader = csv.reader(files)
    for row in reader:
        proxy_list.append(row[0])

for i in proxy_list:
    options = webdriver.ChromeOptions()
    # Отключение режима WebDriver
    options.add_experimental_option('useAutomationExtension', False)
    # # Работа в фоновом режиме
    # options.headless = True
    options.add_argument('--proxy-server=%s' % i)
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver_service = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = webdriver.Chrome(
        service=driver_service,
        options=options
    )
    # Необходимо тестировать!!!
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
              '''
    })
    try:
        driver.get('https://vehiclebid.info')
        driver.close()
        driver.quit()

    except:
        print(f'Прокси {i} не рабочий')
        continue

#
#
# url = 'https://www.enfsolar.com/directory/installer'
# usersagent = {'User-Agent': useragent.random}
# proxy_list = []
# # Перед запуском запускаем scrap_proxy.py для обновления списка проки-серверов
# with open('proxylist.csv', 'r') as files:
#     reader = csv.reader(files)
#     for row in reader:
#         proxy_list.append(row[0])
#
# for i in proxy_list:
#     options = webdriver.ChromeOptions()
#     # Отключение режима WebDriver
#     options.add_experimental_option('useAutomationExtension', False)
#     # # Работа в фоновом режиме
#     # options.headless = True
#     options.add_argument('--proxy-server=%s' % i)
#     driver_service = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
#     driver = webdriver.Chrome(
#         service=driver_service,
#         options=options
#     )
#     try:
#         driver.get(url)
#     except Exception as ex:
#         print(ex)
