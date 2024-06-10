from botasaurus.browser import browser, Driver

import time


@browser
def scrape_heading_task(driver: Driver, data):
    driver.get("https://dexscreener.com/")
    # Переход на страницу google.com

    # Ожидание 20 секунд
    time.sleep(20)

    # Закрытие браузера


scrape_heading_task()
