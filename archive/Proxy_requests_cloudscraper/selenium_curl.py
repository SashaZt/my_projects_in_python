import re
import glob
import json
import os
from bs4 import BeautifulSoup
import shutil
import pickle
import tempfile
import zipfile
import time
import random
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv
def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()

    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--auto-open-devtools-for-tabs")
    s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=chrome_options)
    return driver

def get_selenium():
    driver = get_chromedriver()
    driver.maximize_window()
    url = "https://www.synevo.ua/ua/tests"
    driver.get(url)
    time.sleep(5)
    # Выполните здесь необходимые действия на странице, чтобы сгенерировать запрос

    driver.execute_script("window.close()")

    # Закрытие браузера
    driver.quit()

    # Вывод команды cURL

if __name__ == '__main__':
    get_selenium()