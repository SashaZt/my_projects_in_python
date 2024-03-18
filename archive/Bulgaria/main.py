import os
import time
import threading
import undetected_chromedriver
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv


def get_undetected_chromedriver():
    # Обход защиты
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')

    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument('--headless')
    """Проба"""
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-setuid-sandbox")


    driver = undetected_chromedriver.Chrome()

    return driver


def open_url():
    url = "https://publicbg.mjs.bg/BgSubmissionDoc"
    driver = get_undetected_chromedriver()
    driver.maximize_window()
    driver.get(url)
    next_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@class="btn btn-default g-recaptcha"]')))
    start_button = driver.find_element(By.XPATH, '//input[@class="btn btn-default g-recaptcha"]')
    driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
    return driver

def click_start_button():
    while True:
        now = time.localtime()
        if now.tm_hour == 11 and now.tm_min == 59 and now.tm_sec == 59: # and now.tm_msec == 800: в милисекундах
            for driver in drivers:
                start_button = driver.find_element(By.XPATH, '//input[@class="btn btn-default g-recaptcha"]')
                start_button.click()
            break
        time.sleep(1)

# Создание и запуск 5 потоков
drivers = []
for i in range(5):
    driver = open_url()
    drivers.append(driver)
    t = threading.Thread(target=driver)
    t.start()

# Запуск потока для нажатия на кнопку "start_button" в 11:59:59
t = threading.Thread(target=click_start_button)
t.start()