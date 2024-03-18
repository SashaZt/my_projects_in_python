import csv
import random
import re
import time

import schedule
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()

    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
    s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
      '''
    })
    return driver


def job():
    print("Запускаю get_selenium...")
    get_selenium()


def get_selenium():
    url = 'https://tripoli.land/users/sign_in?sign_in_source=%2Ffarmers'

    driver = get_chromedriver()
    driver.maximize_window()
    driver.get(url)
    wait = WebDriverWait(driver, 60)
    time.sleep(1)
    wait_email = wait.until(
        EC.presence_of_element_located((By.XPATH, '//input[@name="user[email]"]')))
    email = driver.find_element(By.XPATH, '//input[@name="user[email]"]')
    email.send_keys('stepan.onyskiv@gmail.com')
    passwords = driver.find_element(By.XPATH, '//input[@name="user[password]"]')
    passwords.send_keys('Stepan9472')
    passwords.send_keys(Keys.RETURN)
    time.sleep(1)
    coun = 0
    with open('Запоріжжя.csv', 'a', newline='', encoding='utf-8') as file_data:
        writer = csv.writer(file_data, delimiter=';')
        writer.writerow(['', '', '', '', '', '', '', ''])
        for i in range(13, 26):  # 114

            pause_time = random.randint(1, 3)
            driver.get(
                f'https://tripoli.land/farmers/proizvoditeli-zerna/zaporozhie?page={i}&q%5Bcategories_id_eq%5D=2&q%5Bdistrict_region_id_eq%5D=8')
            wait_company = wait.until(
                EC.presence_of_element_located((By.XPATH, '//span[@class="call-popup"]')))
            company = driver.find_element(By.XPATH, '//span[@class="call-popup"]')
            company.click()
            for j in range(1, 41):
                coun += 1
                time.sleep(1)
                time.sleep(pause_time)
                company_nex = driver.find_element(By.XPATH,
                                                  '//button[@class="non-fluid right modal-action-btn tips-tooltip ng-scope"]')
                soup = BeautifulSoup(driver.page_source, 'lxml')
                regex_all = re.compile('beige-hover ng-scope.*')
                telephoni_company = soup.find('table', attrs={'ng-if': '!isMobile()'}).find_all('tbody')[0].find_all(
                    'tr', attrs={'class': regex_all})
                contacts = []
                for i in range(0, len(telephoni_company)):
                    regex_one = re.compile('same-phone-widt.*')
                    try:

                        telef = telephoni_company[i].find('a', attrs={'class': regex_one}).get('ng-href')
                    except AttributeError:
                        telef = ""
                    try:
                        names = telephoni_company[i].find('span', attrs={
                            'class': 'phone-comment phone-comment-edit-pencil tablink-correct tablink-correct hide-hover tips-tooltip ng-binding ng-scope'}).text.strip()
                    except AttributeError:
                        names = ""
                    try:
                        job = telephoni_company[i].find('span', attrs={
                            'class': 'dropdown-toggle position-title tips-tooltip ng-binding'}).text.strip()
                    except AttributeError:
                        job = ""
                    if not telef == "":
                        contacts.append(telef)
                    if not names == "":
                        contacts.append(names)
                    if not job == "":
                        contacts.append(job)
                contacts_email = []

                regex_email = re.compile('beige-hover ng-scope.*')
                try:
                    tables_email = soup.find_all('table', {'class': 'web-phones ng-scope'})
                except:
                    tables_email = None
                try:
                    table = tables_email[1]

                except:
                    table = None
                if not table is None:
                    rows = table.find_all('tr')
                    for row in rows:
                        # Ищем теги 'span' с классом 'ng-binding'
                        spans = row.find_all('span', {'class': 'ng-binding'})
                        for span in spans:
                            # Извлекаем текст из каждого 'span' и добавляем в список
                            contacts_email.append(span.text)

                try:
                    edrpo = soup.find('div', attrs={'ng-if': 'org.erdpou'}).find('div',
                                                                                 attrs={'class': 'ng-binding'}).text
                except:
                    edrpo = None

                address = soup.find('div', attrs={'ng-bind': 'org.address_label'}).text.split(',')
                try:
                    address_company_01 = address[0]
                except:
                    address_company_01 = ""
                try:
                    address_company_02 = address[1]
                except:
                    address_company_02 = ""
                try:
                    address_company_03 = address[2]
                except:
                    address_company_03 = ""
                try:
                    address_company_04 = address[3]
                except:
                    address_company_04 = ""
                try:
                    address_company_05 = address[4]
                except:
                    address_company_05 = ""
                try:
                    address_company_06 = address[5]
                except:
                    address_company_06 = ""
                try:
                    address_company_07 = address[6]
                except:
                    address_company_07 = ""
                try:
                    address_company_08 = address[7]
                except:
                    address_company_08 = ""
                name_company = soup.find('p', attrs={
                    'class': 'modal-title display-inline-block farmer-modal-name ng-binding'}).text
                try:
                    landing_area_sum = soup.find('div',
                                                 attrs={'ng-bind': 'org.landing_area_sum | splitThousands'}).text
                except:
                    landing_area_sum = ""
                try:
                    director = soup.find('div', attrs={'ng-bind': 'org.director'}).text
                except:
                    director = ""
                datas = [address_company_01, address_company_02, address_company_03, address_company_04,
                         address_company_05, address_company_06, address_company_07, address_company_08,
                         name_company, edrpo, director, contacts, contacts_email, landing_area_sum
                         ]
                writer.writerow(
                    datas
                )

                company_nex.click()

        driver.close()
        driver.quit()


# schedule.every().day.at("08:40").do(job)
schedule.every().day.at("22:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
