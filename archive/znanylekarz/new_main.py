import time
import pickle
import csv
import time
from random import randint
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
# Нажатие клавиш
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent

useragent = UserAgent()

# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = webdriver.ChromeOptions()
options.add_argument(
    f"user-agent={useragent.random}"
)
# Отключение режима WebDriver
options.add_argument("--disable-blink-features=AutomationControlled")


# # Работа в фоновом режиме
# options.headless = True
# # Настройка WEB драйвера
# driver_service = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
# driver = webdriver.Chrome(
#     service=driver_service,
#     options=options
# )
# # Окно браузера на весь экран
# driver.maximize_window()


def get_content(url):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"

    }
    # Создаем сначала файл куда будем записывать информацию

    for i in range(1, 2):
        doctor_url = []
        data= []
        # Настройка WEB драйвера
        driver_service = Service(executable_path="C:\scrap_tutorial-master\chromedriver.exe")
        driver = webdriver.Chrome(
            service=driver_service,
            options=options
        )
        # Перебираем все ссылки
        driver.get(url=url + f"&page={i}")
        time.sleep(randint(1, 5))
        table_card = driver.find_elements(By.XPATH,
                                          '//li[contains(@class,"has-cal-active")]//div[@class="media-body"]/h3/a')
        for i in table_card:
            doctor_url.append({'url_name': i.get_attribute("href")})
        for item in doctor_url:
            driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
            for cookie in pickle.load(open("cookies", "rb")):
                driver.add_cookie(cookie)
            driver.implicitly_wait(10)
            driver.refresh()
            driver.implicitly_wait(10)
            specialty_doctor_list = driver.find_elements(By.XPATH,
                                                         '//span[@data-test-id="doctor-specializations"]/a')
            # Получаем специальность доктора
            try:
                specialty_doctor = specialty_doctor_list[0].text.strip()
            except:
                specialty_doctor = "нет специальности"
            # Получаем имя доктора
            name_doctor = driver.find_element(By.XPATH, '//div[@data-id="profile-fullname-wrapper"]').text.strip()
            phone_show = driver.find_element(By.XPATH, '//a[@data-id="show-phone-number-modal"]')
            if phone_show.is_displayed():
                driver.implicitly_wait(5)
                phone_show = driver.find_element(By.XPATH, '//a[@data-id="show-phone-number-modal"]')
                phone_show.click()
                driver.implicitly_wait(5)
                driver.implicitly_wait(5)
                # Если есть похожие елементы, тогда находим все елементы find_elements
                checkbox = driver.find_elements(By.XPATH, '//input[@data-id="gdpr-number-terms-button"]')
                # Нажимаем на N елемент
                checkbox[1].click()
                driver.implicitly_wait(5)
                # Получаем номер телефона
                phone_doctor = driver.find_element(By.XPATH,
                                                   '//a[@data-patient-app-event-name="dp-call-phone"]').text.strip()
            try:
                adres = driver.find_element(By.XPATH, '//span[@itemprop="streetAddress"]').text.strip()
            except:
                adres = "Нет адреса"
            data.append(
                [name_doctor, specialty_doctor, phone_doctor, adres]
            )
            driver.close()
            driver.quit()
    with open("doctor.csv", "w") as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                "Имя",
                "Специальность",
                "Телефон",
                "Адресс"
            )
        )
        writer.writerows(
            data
        )

def parse_content():
    url = "https://www.znanylekarz.pl/szukaj?q=&loc=Warszawa"
    get_content(url)


if __name__ == '__main__':
    parse_content()
