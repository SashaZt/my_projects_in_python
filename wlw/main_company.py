import time

from playwright.sync_api import sync_playwright
import csv


def get_csv_productid():
    csv_filename = 'urls.csv'
    productid_list = []

    with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')

        for row in reader:
            productid_list.append(row)
    return productid_list

def run(playwright):
    urls = get_csv_productid()
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    count = 0
    for u in urls[:10]:
        time.sleep(1)
        count += 1
        url = u[0]
        page.goto(url)

        # Ждем, пока страница полностью загрузится
        page.wait_for_load_state('networkidle')
        # Находим элемент и кликаем по нему
        title_element = page.query_selector('//span[@class="ml-1 title"]')
        if title_element:
            title_element.click()

        # Ждем немного времени после клика, чтобы страница обновилась
        time.sleep(1)  # Снова, лучше использовать методы ожидания Playwright

        # Находим элемент и извлекаем href
        try:
            copy_button = page.query_selector('//a[@class="copy-button"]')
            href = copy_button.get_attribute('href')
        except:
            href = 'Нет телефона'

        # Если предполагается только один элемент h1 для каждой ссылки
        element = page.query_selector("//a[contains(@class, 'company-name')]//h1")
        name_company = element.inner_text()

        print(name_company, href)

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
