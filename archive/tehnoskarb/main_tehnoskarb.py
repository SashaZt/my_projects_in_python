from datetime import datetime
import requests
import json
# from anticaptchaofficial.recaptchav2proxyless import *
import sys
from twocaptcha import TwoCaptcha
import csv

from bs4 import BeautifulSoup
import os
import glob
import time
import undetected_chromedriver as UC

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait

def get_undetected_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')
    # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    s = Service(executable_path=".//chromedriver.exe")
    driver = UC.Chrome(service=s, options=chrome_options)
    # driver.delete_all_cookies()

    return driver

def save_dict():
    folder_path = "./json"

    # Проверяем, существует ли папка json
    if not os.path.exists(folder_path):
        # Если папка не существует, создаем ее
        os.makedirs(folder_path)
    if os.path.exists('tehnoskarb_dict_old.json'):
        os.remove('tehnoskarb_dict_old.json')

    if os.path.exists('tehnoskarb_dict_new.json'):
        os.remove('tehnoskarb_dict_new.json')
    print('Удалили старые файлы словарей')
    # Загрузить страницу
    """Сюда вводим ссылку на товары"""
    url = 'https://ru.tehnoskarb.ua/instrumenty-i-oborudovanie/c49/filter/new=1;vendor=19,35,64,95,97,370476'
    coun = 0
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    script_tag = soup.find('script', string=lambda text: text and '__INITIAL_STATE__=' in text)
    script_content = script_tag.string.replace('__INITIAL_STATE__=', '').strip().replace('window.', '')
    json_content = json.loads(script_content)
    total_items = json_content["Catalog"]["catalog"]["total"]
    items_in_page = json_content["Catalog"]["catalog"]["recordOnPage"]
    range_list = total_items // items_in_page
    if total_items % items_in_page != 0:  # если деление имеет остаток
        range_list += 1

    for i in range(range_list + 1):
        time.sleep(1)
        coun += 1
        if i == 1:
            response = requests.get(url)
            time.sleep(5)
            # Создать объект BeautifulSoup
            soup = BeautifulSoup(response.text, 'lxml')

            # Найти тег <script> и извлечь его содержимое
            script_tag = soup.find('script', string=lambda text: text and '__INITIAL_STATE__=' in text)
            script_content = script_tag.string.replace('__INITIAL_STATE__=', '').strip().replace('window.', '')
            json_content = json.loads(script_content)
            # print(json_content)
            with open(f'./json/tehnoskarb_{i}.json', 'w', encoding='utf-8') as f:
                json.dump(json_content, f, indent=4, ensure_ascii=False)
        if i > 1:
            time.sleep(5)
            response = requests.get(f'{url}?page={i}')
            soup = BeautifulSoup(response.text, 'lxml')
            script_tag = soup.find('script', string=lambda text: text and '__INITIAL_STATE__=' in text)
            script_content = script_tag.string.replace('__INITIAL_STATE__=', '').strip().replace('window.', '')
            json_content = json.loads(script_content)
            with open(f'./json/tehnoskarb_{i}.json', 'w', encoding='utf-8') as f:
                json.dump(json_content, f, indent=4, ensure_ascii=False)
    targetPattern = r"./json/*.json"
    files_json = glob.glob(targetPattern)
    datas = []
    result_dict = {}
    for item in files_json:
        with open(item, encoding='utf-8') as f:
            data = json.load(f)
            models = data['Catalog']['catalog']['models']
            for item in models:
                if 'full' in item:
                    result_dict[item['id']] = {
                        'full': item['full'],
                        'url': f"https://ru.tehnoskarb.ua{item['url']}",
                        'count': item['count']
                    }
                # with open(f'tehnoskarb_dict.json', 'a') as f:
                #     json.dump(result_dict, f, indent=4, ensure_ascii=False)
    with open(f'tehnoskarb_dict_old.json', 'w') as f:
        json.dump(result_dict, f, indent=4, ensure_ascii=False)
    if os.path.exists('tehnoskarb_dict_old.json'):
        folder_path = r"./json/"
        files = os.listdir(folder_path)
        for file in files:
            file_path = os.path.join(folder_path, file)
            os.remove(file_path)
    print("Сохранил словарь всех позицей")

def update_dict():
    # Загрузить страницу
    url = 'https://ru.tehnoskarb.ua/instrumenty-i-oborudovanie/c49/filter/new=1;vendor=19,35,64,95,97,370476'
    coun = 0
    response = requests.get(url)
    # Создать объект BeautifulSoup
    soup = BeautifulSoup(response.text, 'lxml')

    # Найти тег <script> и извлечь его содержимое
    script_tag = soup.find('script', string=lambda text: text and '__INITIAL_STATE__=' in text)
    script_content = script_tag.string.replace('__INITIAL_STATE__=', '').strip().replace('window.', '')
    json_content = json.loads(script_content)
    total_items = json_content["Catalog"]["catalog"]["total"]
    items_in_page = json_content["Catalog"]["catalog"]["recordOnPage"]
    range_list = total_items // items_in_page
    if total_items % items_in_page != 0:  # если деление имеет остаток
        range_list += 1

    for i in range(range_list + 1):
        time.sleep(1)
        coun += 1
        if i == 1:
            response = requests.get(url)
            # Создать объект BeautifulSoup
            soup = BeautifulSoup(response.text, 'lxml')

            # Найти тег <script> и извлечь его содержимое
            script_tag = soup.find('script', string=lambda text: text and '__INITIAL_STATE__=' in text)
            script_content = script_tag.string.replace('__INITIAL_STATE__=', '').strip().replace('window.', '')
            json_content = json.loads(script_content)
            # print(json_content)
            with open(f'./json/tehnoskarb_{i}.json', 'a', encoding='utf-8') as f:
                json.dump(json_content, f, indent=4, ensure_ascii=False)
        if i > 1:
            response = requests.get(f'{url}?page={i}')
            # Создать объект BeautifulSoup
            soup = BeautifulSoup(response.text, 'lxml')

            # Найти тег <script> и извлечь его содержимое
            script_tag = soup.find('script', string=lambda text: text and '__INITIAL_STATE__=' in text)
            script_content = script_tag.string.replace('__INITIAL_STATE__=', '').strip().replace('window.', '')
            json_content = json.loads(script_content)
            with open(f'./json/tehnoskarb_{i}.json', 'a', encoding='utf-8') as f:
                json.dump(json_content, f, indent=4, ensure_ascii=False)
    targetPattern = r"./json/*.json"
    files_json = glob.glob(targetPattern)
    datas = []
    result_dict = {}
    for item in files_json:
        with open(item, encoding='utf-8') as f:
            data = json.load(f)
            models = data['Catalog']['catalog']['models']
            # print(models)
            # Создаем пустой словарь для хранения данных

            for item in models:
                if 'full' in item:
                    result_dict[item['id']] = {
                        'full': item['full'],
                        'url': f"https://ru.tehnoskarb.ua{item['url']}",
                        'count': item['count']
                    }
                # with open(f'tehnoskarb_dict.json', 'a') as f:
                #     json.dump(result_dict, f, indent=4, ensure_ascii=False)
    with open(f'tehnoskarb_dict_new.json', 'w') as f:
        json.dump(result_dict, f, indent=4, ensure_ascii=False)
    if os.path.exists('tehnoskarb_dict_new.json'):
        folder_path = r"./json/"
        # Получаем список файлов в папке
        files = os.listdir(folder_path)

        # Проходимся по всем файлам и удаляем их
        for file in files:
            file_path = os.path.join(folder_path, file)
            os.remove(file_path)
    print("Получил словарик новинок")
def check_news_product():
    now = datetime.now()
    formatted_date = now.strftime("%H:%M %d.%m.%Y")
    with open(f'tehnoskarb_dict_old.json') as f:
        tehnoskarb_dict_old = json.load(f)
    with open(f'tehnoskarb_dict_new.json') as f:
        tehnoskarb_dict_new = json.load(f)
    url = 'https://ru.tehnoskarb.ua/instrumenty-i-oborudovanie/c49/filter/new=1;vendor=19,35,64,95,97,370476'
    url_new_product = []
    for item_id in tehnoskarb_dict_new:
        if item_id not in tehnoskarb_dict_old and tehnoskarb_dict_new[item_id]["count"] == 1:
            url_new_product.append(tehnoskarb_dict_new[item_id]["url"])
    print(f"Количевство новых позицей {len(url_new_product)} в {formatted_date}")

    if len(url_new_product) != 0:
        reserved = False
        for item in url_new_product:
            response = requests.get(item)
            soup_id = BeautifulSoup(response.text, 'lxml')
            script_tag_id = soup_id.find('script', string=lambda text: text and '__INITIAL_STATE__=' in text)
            script_content = script_tag_id.string.replace('__INITIAL_STATE__=', '').strip().replace('window.', '')
            json_content_id = json.loads(script_content)
            id_product_id = json_content_id['Catalog']['catalog']['models'][0]['id']
            try:
                with open('product.csv', newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=';')
                    for row in reader:
                        if row[0] == id_product_id:
                            print('Товар уже резервировался!')
                            reserved = True
                            break  # выходим из внутреннего цикла
                    if reserved:
                        break  # выходим из внешнего цикла
            except:
                print("Товар еще не резервировали")
            if not reserved:
                driver = get_undetected_chromedriver(use_proxy=False,
                                                     user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
                driver.get(item)  # 'url_name' - это и есть ссылка
                driver.maximize_window()
                time.sleep(1)
                soup = BeautifulSoup(driver.page_source, 'lxml')

                # Найти тег <script> и извлечь его содержимое
                script_tag = soup.find('script', string=lambda text: text and '__INITIAL_STATE__=' in text)
                script_content = script_tag.string.replace('__INITIAL_STATE__=', '').strip().replace('window.', '')
                json_content = json.loads(script_content)
                url_product = json_content['Catalog']['catalog']['models'][0]['url']
                id_product = json_content['Catalog']['catalog']['models'][0]['id']

                url = f'https://ru.tehnoskarb.ua/{url_product}'
                name_product = json_content['Catalog']['catalog']['models'][0]['full']
                price_product = json_content['Catalog']['catalog']['models'][0]['max']
                """ТЕСТОВЫЙ ВАРИАНТ если предложение 1"""
                try:

                    kliks_in_one_klik_wait = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[@class="btn-fast-order"]')))
                    kliks_in_one_klik = driver.find_element(By.XPATH, '//button[@class="btn-fast-order"]')
                    kliks_in_one_klik.click()
                    time.sleep(2)
                    result = driver.execute_script('''
                        function findRecaptchaClients() {
                          if (typeof (___grecaptcha_cfg) !== 'undefined') {
                            return Object.entries(___grecaptcha_cfg.clients).map(([cid, client]) => {
                              const data = { id: cid, version: cid >= 10000 ? 'V3' : 'V2' };
                              const objects = Object.entries(client).filter(([_, value]) => value && typeof value === 'object');
    
                              objects.forEach(([toplevelKey, toplevel]) => {
                                const found = Object.entries(toplevel).find(([_, value]) => (
                                  value && typeof value === 'object' && 'sitekey' in value && 'size' in value
                                ));
    
                                if (typeof toplevel === 'object' && toplevel instanceof HTMLElement && toplevel['tagName'] === 'DIV'){
                                    data.pageurl = toplevel.baseURI;
                                }
    
                                if (found) {
                                  const [sublevelKey, sublevel] = found;
    
                                  data.sitekey = sublevel.sitekey;
                                  const callbackKey = data.version === 'V2' ? 'callback' : 'promise-callback';
                                  const callback = sublevel[callbackKey];
                                  if (!callback) {
                                    data.callback = null;
                                    data.function = null;
                                  } else {
                                    data.function = callback;
                                    const keys = [cid, toplevelKey, sublevelKey, callbackKey].map((key) => `['${key}']`).join('');
                                    data.callback = `___grecaptcha_cfg.clients${keys}`;
                                  }
                                }
                              });
                              return data;
                            });
                          }
                          return [];
                        }
                        return findRecaptchaClients();
                    ''')
                    callback_value = result[0]['callback']
                    telef = driver.find_elements(By.XPATH, '//input[@class="base-text-field__input"]')[1]
                    """ Сюда вводим свой номер телефона"""
                    telef.send_keys('0676666666')
                    photo = driver.find_element(By.XPATH, '//span[@class="base-checkbox__check d-if jc-c ai-c fl-sh-0"]')
                    photo.click()
                    """Сюда вводим token с сайта https://2captcha.com/"""
                    solver = TwoCaptcha('3b3f94fa22b7aa6de50b79adfb85c851')
                    result = solver.recaptcha(
                        sitekey="6Ld1rjQUAAAAAByG3eUucDd3_y_8wjFBLHj0gv_G",
                        url=driver.current_url)
                    code = str(result['code'])
                    while not code:
                        time.sleep(10)
                        result = solver.recaptcha(
                            sitekey="6Ld1rjQUAAAAAByG3eUucDd3_y_8wjFBLHj0gv_G",
                            url=driver.current_url)
                        code = str(result['code'])
                    print(f"Код решен")
                    # выполнить callback с токеном
                    # driver.execute_script("""
                    #                     document.querySelector('#g-recaptcha-response').value = arguments[0];
                    #                     ___grecaptcha_cfg.clients['0']['B']['B']['callback'](arguments[0]);
                    #                 """, code)
                    driver.execute_script(f"""
                        document.querySelector('#g-recaptcha-response').value = arguments[0];
                        {callback_value}(arguments[0]);
                    """, code)
                    counter_wait_url = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[@class="fast-order-btn"]')))
                    wait_telefone = driver.find_element(By.XPATH, '//button[@class="fast-order-btn"]')
                    wait_telefone.click()
                    print('Вы зарезервировали товар!')
                    with open(f"product.csv", "a",
                              errors='ignore', encoding="utf-8") as file:
                        writer = csv.writer(file, delimiter=";", lineterminator="\r")
                        writer.writerow(
                            (
                                id_product, name_product, price_product, url, formatted_date
                            )
                        )
                    driver.close()
                    driver.quit()
                except:
                    print('Товар уже выкуплен')
                    driver.close()
                    driver.quit()
                    continue
    else:
        print("Предложений нет!")



if __name__ == '__main__':
    while True:
        save_dict()
        print("Пауза 5 мин")
        time.sleep(10)  # пауза на 5 минут
        update_dict()
        check_news_product()
