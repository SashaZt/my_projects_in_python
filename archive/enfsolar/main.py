import csv
import time

# Нажатие клавиш
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

useragent = UserAgent()
options = webdriver.ChromeOptions()
# Отключение режима WebDriver
options.add_experimental_option('useAutomationExtension', False)
# # Работа в фоновом режиме
# options.headless = True
options.add_argument(
    # "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
    f"user-agent={useragent.random}"
)
driver_service = Service(executable_path="/chromedriver.exe")
driver = webdriver.Chrome(
    service=driver_service,
    options=options
)


# # Окно браузера на весь экран
# driver.maximize_window()


# Для работы webdriver____________________________________________________


# Для работы undetected_chromedriver ---------------------------------------

# import undetected_chromedriver as uc
# driver = uc.Chrome()


# Для работы undetected_chromedriver ---------------------------------------


# "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0"

def get_content(url):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"

    }

    try:
        url_country = []
        url_firma = []
        resp = requests.get(url, headers=header)
        soup = BeautifulSoup(resp.text, 'lxml')
        table = soup.find('div', class_='mk-body')
        table_continent = table.find_all('div', class_='clearfix mk-section')
        for i in table_continent:
            driver.implicitly_wait(5)
            country_list = i.find_all('li', class_='pull-left')
            for j in country_list:
                href = 'https://www.enfsolar.com' + j.find_next('a').get("href")
                url_country.append(href)

        for item in url_country[0:1]:
            driver.implicitly_wait(5)
            driver.get(f'{item}')
            country = item.split("/")[-1]
            # Листать по страницам ---------------------------------------------------------------------------
            isNextDisable = False
            while not isNextDisable:
                try:
                    soup = BeautifulSoup(driver.page_source, 'lxml')
                    table_firma = soup.find('table', attrs={'class': 'enf-list-table'})
                    # Получаем таблицу всех фирм на странице
                    firma_url = table_firma.find('tbody').find_all('tr')
                    # Получаем ссылку на каждую фирму
                    for href in firma_url:
                        url = href.find_next('td').find('a').get("href")
                        # Добавляем ссылки на фирмы в список
                        url_firma.append(url)
                    time.sleep(5)
                    # Если необходимо подождать елемент тогда WebDriverWait
                    # next_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//i[@class="fa fa-chevron-right"]')))
                    next_button = driver.find_element(By.XPATH, '//i[@class="fa fa-chevron-right"]')
                    # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!
                    if next_button[0:1]:
                        next_button.click()
                    else:
                        isNextDisable = True
                except:
                    isNextDisable = True
            # Листать по страницам ---------------------------------------------------------------------------
        with open("countrys_firma.csv", "w", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    'Название фирмы',
                    'Адрес фирмы',
                    'Телефон фирмы',
                    'Email фирмы',
                    'Сайт фирмы',
                    'Страна'
                )
            )
        for href_url in url_firma:
            driver.get(f"{href_url}")
            try:
                name_firma = driver.find_element(By.XPATH, '//h1[@itemprop="name"]').text
            except:
                name_firma = 'Нет названия фирмы'
            try:
                adress_firma = driver.find_element(By.XPATH, '//td[@itemprop="address"]').text
            except:
                adress_firma = 'Нет адресса фирмы'
            try:
                # Получение информации с атрибута, атрибут можно найти на вкладке Properties
                tel_firma_ = driver.find_element(By.XPATH, '//td[@itemprop="telephone"]').click()
                time.sleep(1)
                tel_firma = driver.find_element(By.XPATH, '//td[@itemprop="telephone"]').get_attribute('outerText')
            except:
                tel_firma = 'Нет телефона фирмы'
            try:
                email_firma_ = driver.find_element(By.XPATH, '//td[@itemprop="email"]').click()
                time.sleep(1)
                email_firma = driver.find_element(By.XPATH, '//td[@itemprop="email"]').get_attribute('outerText')
            except:
                email_firma = 'Нет email фирмы'
            try:
                www_firma = driver.find_element(By.XPATH, '//a[@itemprop="url"]').get_attribute('outerText')
            except:
                www_firma = 'Нет сайта фирмы'
            try:
                countrys_firma = driver.find_elements(By.XPATH, '//span[@itemprop="name"]')
                country_firma = countrys_firma[1].text
            except:
                countrys_firma = 'Нет страны фирмы'
            with open("countrys_firma.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow(
                    (
                        name_firma,
                        adress_firma,
                        tel_firma,
                        email_firma,
                        www_firma,
                        country
                    )
                )



    except Exception as ex:
        print(ex)

    finally:
        driver.close()
        driver.quit()


def parse_content():
    url = "https://www.enfsolar.com/directory/installer"
    get_content(url)


if __name__ == '__main__':
    parse_content()
