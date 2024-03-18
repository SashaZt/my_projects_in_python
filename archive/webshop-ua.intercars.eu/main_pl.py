import concurrent.futures
import random
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright
import csv
from proxi import proxies


def prepare_data(row):
    # name_product =
    name_product_find = f"{row[1]} {row[0]}"
    name_file = name_product_find.replace(" ", "_")
    """Изменить на e:/intercars_html"""
    file_path = Path('e:/intercars_html') / f'{name_file}.html'
    if file_path.exists():
        return None  # Пропускаем файл, если он уже существует
    else:
        proxy = get_random_proxy(load_proxies("proxy.txt"))
        return name_product_find, name_file, proxy


async def process_row(data):
    if data is None:
        return
    name_product_find, name_file, proxy = data
    """Изменить на e:/intercars_html"""
    file_path = Path('e:/intercars_html') / f'{name_file}.html'

    proxy_parts = proxy.split('@')
    login_password, ip_port = proxy_parts[0], proxy_parts[1]
    login, password = login_password.split(':')
    ip, port = ip_port.split(':')
    proxy_url = f'http://{login}:{password}@{ip}:{port}'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, proxy={"server": proxy_url})
        page = await browser.new_page(viewport=None)
        await page.goto(url)  # замените на вашу начальную страницу
        try:
            find_product = await page.wait_for_selector('xpath=//input[@class="ui-autocomplete-input"]', state="attached",
                                                        timeout=10000)
            # Очистка поля
            await find_product.fill('')

            # Ввод данных в другое поле
            await page.fill('name=name_product_find', name_product_find)

            # Нажатие Enter
            await page.press('name=name_product_find', 'Enter')
            await asyncio.sleep(1)

            try:
                await page.wait_for_selector('xpath=//div[contains(text(), "Немає результатів")]')
            except:
                button_img_wain = await page.wait_for_selector('xpath=//div[@class="art-images margincenter"]',
                                                               state="attached", timeout=10000)
                await button_img_wain.click()
                wait_img_full = await page.wait_for_selector('xpath=//div[@class="swal2-container"]', state="attached",
                                                             timeout=10000)
                await asyncio.sleep(1)
                name_brand_find = name_product_find.split(' ')[0]
                element_handle = await page.wait_for_selector('xpath=//span[@id="manufacture_30"]')
                brand_product = await element_handle.inner_text()

                if name_brand_find == brand_product:
                    html_content = await page.content()
                    with open(file_path, "w", encoding='utf-8') as file:
                        file.write(html_content)
                    # Открываем (или создаем) CSV-файл для записи
                    with open('logs_compliance.csv', 'a', newline='') as csvfile:
                        logwriter = csv.writer(csvfile, delimiter=';')
                        logwriter.writerow([file_path, name_product_find])

        except Exception as e:
            save_error_to_csv(name_file)
        finally:
            await browser.close()

def load_proxies(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if '@' in line and ':' in line]
    except FileNotFoundError:
        return []

# Получение случайного прокси
def get_random_proxy(proxies):
    return random.choice(proxies) if proxies else None
async def save_link_all_product(url):
    # Загрузка данных CSV
    with open(f'C:\\scrap_tutorial-master\\webshop-ua.intercars.eu\\csv\\output.csv', newline='',
              encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=';', quotechar='|'))

    sem = asyncio.Semaphore(8)  # Ограничиваем количество параллельных задач до 8

    async def process_row_with_semaphore(data):
        async with sem:
            await process_row(data)

    async def process_batch(batch):
        tasks = [process_row_with_semaphore(prepare_data(row)) for row in batch]
        await asyncio.gather(*tasks)

    # Разделение данных на пакеты и их обработка
    for start in range(268200, len(csv_reader), 100):
        end = start + 100
        batch = csv_reader[start:end]
        await process_batch(batch)
        with open('log.txt', 'a') as f:
            print(end, file=f)


def save_error_to_csv(name_file):
    with open('errors.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([name_file])
        print(f'Записано {name_file}')


if __name__ == "__main__":
    url = "https://webshop-ua.intercars.eu/zapchasti/"
    loaded_proxies = load_proxies("proxy.txt")  # Загрузка прокси-серверов
    asyncio.run(save_link_all_product(url, loaded_proxies))  # Передача списка в асинхронную функцию

