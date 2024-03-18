from playwright.sync_api import sync_playwright
import os
import re
import time
import csv
current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
bd_path = os.path.join(temp_path, 'bd')
list_path = os.path.join(temp_path, 'list')
product_path = os.path.join(temp_path, 'product')
def is_valid_email(email):
    # Исключаем строки, похожие на расширения файлов
    if re.search(r'\.[a-zA-Z]{2,4}\.[a-zA-Z]{2,4}$', email):
        return False

    # Расширенное регулярное выражение для проверки валидности email
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return pattern.match(email)

def get_csv_sel():
    csv_filename = 'sel.csv'
    productid_list = []

    with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        for row in reader:
            productid_list.append(row[1])
    return productid_list
def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('https://www.google.com/')
    time.sleep(1)
    mail = 'mail'

    csv_data = get_csv_sel()

    with open('emails_found.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Search Term', 'Emails'])

        for i in csv_data[2:]:
            safe_i = re.sub(r'[^a-zA-Z0-9]', '_', i)
            file_html = os.path.join(product_path, f'{safe_i}.html')
            if not os.path.exists(file_html):
                page.fill('textarea[type="search"]', f'{i} {mail}')
                page.press('textarea[type="search"]', 'Enter')
                time.sleep(2)  # Дать время странице на загрузку

                selectors = [
                    "xpath=/html/body/div[5]/div/div[10]/div[1]/div[2]/div[2]/div/div/div[1]",
                    "xpath=/html/body/div[5]/div/div[10]/div[1]/div[2]/div[2]/div/div/div[2]",
                    "xpath=/html/body/div[5]/div/div[10]/div[1]/div[2]/div[2]/div/div/div[3]"
                ]

                emails = set()
                for selector in selectors:
                    element_handle = page.query_selector(selector)
                    if element_handle:
                        element_content = element_handle.text_content()
                        found_emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', element_content)
                        emails.update(found_emails)

                # Запись результатов в CSV
                if emails:
                    writer.writerow([i, ';'.join(emails)])
                else:
                    writer.writerow([i, '0 emails'])

                with open(file_html, "w", encoding='utf-8') as f:
                    f.write(page.content())

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
