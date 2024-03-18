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

    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    # chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    # chrome_options.add_argument('--disable-extensions') # Отключает использование расширений
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-setuid-sandbox')
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
def get_selenium():
    url = 'https://www.reddit.com/account/login/?experiment_d2x_safari_onetap=enabled&experiment_d2x_google_sso_gis_parity=enabled&experiment_d2x_am_modal_design_update=enabled&experiment_mweb_sso_login_link=enabled&shreddit=true&use_accountmanager=true'

    driver = get_chromedriver()
    driver.maximize_window()
    driver.get(url)
    login_reddit = 'ZombieAffectionate76'
    pass_reddit = 't9T%gyh5sv~w~r&'
    wait = WebDriverWait(driver, 60)
    # button_login = driver.find_element(By.XPATH, '//span[@class="flex items-center gap-xs"]')
    # wait_input_email = wait.until(
    #     EC.presence_of_element_located((By.XPATH, '//input[@name="username"]')))
    input_email = driver.find_element(By.XPATH, '//input[@name="username"]')
    input_email.send_keys(login_reddit)
    input_pass = driver.find_element(By.XPATH, '//input[@name="password"]')
    input_pass.send_keys(pass_reddit)
    time.sleep(1)
    button_log_in = driver.find_element(By.XPATH, '//button[@class="AnimatedForm__submitButton m-full-width m-modalUpdate "]').click()
    # input_pass.send_keys(Keys.RETURN)
    time.sleep(10)
    url = 'https://www.reddit.com/r/AskReddit/comments/15b1p0j/what_would_you_like_to_repeat_in_your_life/?utm_source=share&utm_medium=web2x&context=3'
    driver.get(url)
    wait_input_email = wait.until(
        EC.presence_of_element_located((By.XPATH, '//button[@data-click-id="upvote"]')))
    button_like = driver.find_elements(By.XPATH, '//button[@data-click-id="upvote"]')
    post_like = button_like[0].click()
    time.sleep(2)
    comment_like = button_like[1].click()
    time.sleep(10)

if __name__ == '__main__':
    get_selenium()
