import csv
import time

from playwright.sync_api import sync_playwright


def extract_links(page, xpath):
    elements = page.query_selector_all(xpath)
    links = [element.get_attribute('href') for element in elements]
    return links


def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()

    with open('emails_found.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        for i in range(1, 95):
            url = 'https://www.wlw.de/de/suche?q=transportlogistik' if i == 1 else f'https://www.wlw.de/de/suche/page/{i}?q=transportlogistik'
            page.goto(url)
            time.sleep(1)  # Использование time.sleep не рекомендуется для ожидания загрузки страницы

            links = extract_links(page, '//div[@data-test="company"]//a[@data-test="company-name"]')
            for href in links:
                writer.writerow([href])

        browser.close()


with sync_playwright() as playwright:
    run(playwright)
