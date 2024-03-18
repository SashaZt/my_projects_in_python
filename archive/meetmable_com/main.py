from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pickle

import re
import os
import requests
import csv
import json
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver

def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--auto-open-devtools-for-tabs=devtools://devtools/bundled/inspector.html')

    s = Service(
        executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )

    return driver


def get_brands():
    """Получаем бренды"""
    with open('urls_brand.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['url', 'api_url'])  # добавляем второй заголовок

        with open('brands.json', 'r', encoding="utf-8") as f:
            data = json.load(f)

            for seller in data['sellers']:
                url = f"https://www.meetmable.com/{seller['slug']}"
                api_url = f"https://api.meetmable.com/v1/search?include=variants%2CproductsForVariants%2Cfilters%2Csellers&page=1&pageSize=100&sellerSlug={seller['slug']}&respectCustomSellerFilters=true&useNewSearch=false"
                writer.writerow([url, api_url])  # записываем их в csv

def get_products():
    """Получаем продукты"""
    with open('urls_brand.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        count = 0
        for row in reader:
            url = row[1]
            brands = row[0].split('/')[-1]
            # отправляем POST-запрос на URL и получаем JSON
            response = requests.post(url, json={})
            json_data = json.loads(response.content)

            # сохраняем полученный JSON в файл с именем brands
            with open(f'C:\\scrap_tutorial-master\\meetmable_com\\json_products\\{brands}.json', mode='w', encoding='utf-8') as file:
                json.dump(json_data, file, ensure_ascii=False, indent=2)
            count += 1
            print(count)
            time.sleep(10)

    #         driver = get_chromedriver()
    #         driver.get(url)
    #         time.sleep(5)
    #         driver.execute_script('''
    #                var elements = document.querySelectorAll('[aria-label="Network panel"]');
    #                for (var i = 0; i < elements.length; i++) {
    #                    var element = elements[i];
    #                    if (element.offsetWidth > 0 && element.offsetHeight > 0) {
    #                        element.click();
    #                        break;
    #                    }
    #                }
    #            ''')
    #         time.sleep(5)
    #         requests = driver.execute_script('''
    #                var performanceEntries = performance.getEntriesByType("resource");
    #                var fetchRequests = [];
    #                for (var i=0; i < performanceEntries.length; i++) {
    #                    var entry = performanceEntries[i];
    #                    if (entry.initiatorType === 'fetch' || entry.initiatorType === 'xmlhttprequest') {
    #                        fetchRequests.push(entry);
    #                    }
    #                }
    #                return fetchRequests;
    #            ''')
    #         response_list = []
    #         for request in requests:
    #             print(request)
    #         #     if request['initiatorType'] in ['fetch', 'xmlhttprequest']:
    #         #         response = requests.get(request[0])
    #         #         response_list.append(response)
    #         # print(response_list)
    #         # urls_product = []
    #         # for request in requests:
    #         #     print(request)
    # #             if "https://api.meetmable.com/v1/" in request['name']:
    # #                 response = requests.get(request['name'])
    # #                 response_list.append(response)
    # #
    # # print(response_list)



def get_url_product():
    path_to_json = 'C:\scrap_tutorial-master\meetmable_com\json_products'
    # Получаем список файлов в папке
    # открываем файл для записи
    folder_path = "json_products"
    output_file = "product_links.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)

        # записываем заголовок CSV файла
        writer.writerow(["product_url"])

        # итерируемся по всем файлам в папке
        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                # открываем файл JSON
                with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as json_file:

                    data = json.load(json_file)

                    # итерируемся по каждому элементу в списке variants
                    for variant in data["variants"]:
                        # получаем ссылку на детальную страницу продукта
                        detail_page_url = f'https://www.meetmable.com/{variant["links"]["detailPage"]}'
                        # записываем ссылку в CSV файл
                        writer.writerow([detail_page_url])



def get_json_product():
    # Открываем файл product_links.csv
    driver = get_chromedriver()
    auth_token = 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik9EVTJORGxFTkVJeE9ETkRRVVpDUmtGQk1FSXdNMFJDTlVFME9EWkJNak0wUXpFMlFVTXlOZyJ9.eyJpc3MiOiJodHRwczovL2F1dGgubWVldG1hYmxlLmNvbS8iLCJzdWIiOiJhdXRoMHw2NDNlN2I1YzgyZGZiNGY2NjEwNTFjNzEiLCJhdWQiOlsiYXBpLm1lZXRtYWJsZS5jb20iLCJodHRwczovL21hYmxlLmF1dGgwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE2ODMxMTIxMjQsImV4cCI6MTY4MzE5ODUyNCwiYXpwIjoiUDBqN0dVMW5vQnAxZTBpSU5JMUFNSENvdWJQbVpKSWwiLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIG9mZmxpbmVfYWNjZXNzIiwiZ3R5IjoicGFzc3dvcmQiLCJwZXJtaXNzaW9ucyI6WyJidXllciIsImJ1eWVyczpyZWFkIiwiYnV5ZXJzOndyaXRlIiwic2VsbGVyczpyZWFkIl19.h5a6bzyut9ssNt_lg1GUGH6CC9oLvUKzJPOtNeC787HnZbyjV01HmNw6Sxo_xvS_WKrwGRxe8w3YjBQzOR_NGcYKnzyB-6szN71_Cq9X6Ldy4vIK86bqIVwrAhIh0EWT5iVRysByWx8eItXPZ4ufP3o5oDshnxVDYZGBg8PD9ai-4L_ndUi3fihFNIozuXb93kVo9PcFLb0ZnnvhnwY5Fap1qO8QTNWApXdlxfD_wk_0hlAWP9GsdZJAVCfjPO9vdDzduRsic-xlOt_mUAcHUM3rNYq_mjx2lWiQU80FRBNTAuLuAa8-3vhPUCMZbl0WNihNxpCocNglhIjfK81irA'
    headers = {'Authorization': auth_token}
    driver.execute_cdp_cmd('Network.enable', {})
    driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': headers})
    driver.get('https://www.meetmable.com/sign-in')
    time.sleep(5)
    login = 'sales@firstdealsclub.com'
    pass_ = 'Aa!56082815608281'
    # Находим поле ввода логина и вводим в него значение
    input_login = driver.find_element(By.XPATH, '//input[@name="email"]')
    input_login.send_keys(login)

    # Находим поле ввода пароля и вводим в него значение
    input_pass = driver.find_element(By.XPATH, '//input[@name="password"]')
    input_pass.send_keys(pass_)

    # Отправляем форму входа, нажимая на кнопку "Войти" (если такая есть)
    input_pass.send_keys(Keys.RETURN)
    time.sleep(5)
    # exit()
    with open('product_links.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        # Читаем каждую строку

        count = 0
        for row in reader:
            # Первый элемент строки содержит URL
            url = row[0]
            group = row[0].split('/')[-3]
            folder_path =  "c:\\data_meetmable_com"
            for filename in os.listdir(folder_path):
                # проверяем, что имя файла начинается с числа, а затем идет "_171849.html"
                if re.match(fr'^\d+_{group}\.html$', filename):
                    # файл найден, пропускаем итерацию
                    continue
                else:
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

                    # Ожидание загрузки списка запросов
                    time.sleep(5)

                    # Получение списка запросов
                    requests = driver.execute_script('''
                        var performanceEntries = performance.getEntriesByType("resource");
                        var fetchRequests = [];
                        for (var i=0; i < performanceEntries.length; i++) {
                            var entry = performanceEntries[i];
                            if (entry.initiatorType === 'fetch' || entry.initiatorType === 'xmlhttprequest') {
                                fetchRequests.push(entry);
                            }
                        }
                        return fetchRequests;
                    ''')
                    # urls_product = []
                    # Вывод списка запросов

                    for request in requests:
                        if "https://api.meetmable.com/v1/products/" in request['name']:
                            url_product = request['name']
                            # print(url_product)
                            #
                            product_id = re.search(r'/(\d+)\?', url_product).group(1)
                            driver.get(url_product)
                            page_content = driver.page_source
                            json_str =re.sub('<.*?>', '', page_content).replace('\n', '').replace('\\', '\\\\')
                            with open(f'c:\\data_meetmable_com\\{count}_{product_id}.html', 'w', encoding='utf-8') as f:
                                f.write(page_content)
                            # if json_str.startswith('{') or json_str.startswith('['):
                            #     # преобразуем строку в объект Python
                            #     data = json.loads(json_str)
                            #     # json_data = json.loads(data)
                            #     # print(json_data)
                            # else:
                            #     print('Ошибка: входная строка не является корректным JSON-объектом.')
                            #
                            # # # print(page_content)
                            # # # time.sleep(60)
                            # # сохраняем JSON в файл
                            # with open(f'C:\\scrap_tutorial-master\\meetmable_com\\json_products\\{product_id}.json', 'w', encoding='utf-8') as file:
                            #     json.dump(data, file, indent=4, ensure_ascii=False)
                    count += 1
                    print(count)
                # ti/me.sleep(5)
        driver.quit()
        driver.close()
        #









    """Рабочий"""
    # driver.execute_script('window.open("devtools://devtools/bundled/inspector.html");')
    # driver.switch_to.window(driver.window_handles[-1])
    # driver.execute_script('window.network = performance.getEntriesByType("resource").map((resource) => resource.name);')
    # requests = driver.execute_script('return window.network;')
    # print(requests)


if __name__ == '__main__':
    # get_brands()
    # get_products()
    # get_url_product()
    get_json_product()