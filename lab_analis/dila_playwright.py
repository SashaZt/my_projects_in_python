import asyncio
import os
import csv
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://dila.ua/price.html?tab=panels")
        await page.click('xpath=//div[@id="dilaModalCity"]//div[@class="dila-modal-body"]//a[@class="chosen-single"]')
        await asyncio.sleep(1)
        await page.click('xpath=//li[@data-option-array-index="1"]')
        # Цикл, который будет кликать на элемент, пока он видим
        # """//*[contains(@class, 'analizes-list-item')]"""
        await asyncio.sleep(1)
        page_content = await page.content()

        # Сохраняем содержимое страницы в файл
        with open("page_content.html", "w", encoding="utf-8") as file:
            file.write(page_content)
        # element = await page.query_selector("xpath=//div[@id='analizes-list']")
        #
        # if element:
        #     # Поиск всех дочерних элементов внутри найденного элемента
        #     child_elements = await element.query_selector_all("xpath=//*[contains(@class, 'analizes-list-item')]")
        #     print(f"Найдено {len(child_elements)} элементов.")
        #
        #     # Дополнительные действия с дочерними элементами
        #     for child in child_elements:
        #         # Например, получить текст каждого элемента
        #         text = await child.inner_text()
        #         print(text)
        #
        # else:
        #     print("Элемент не найден")


        # for category_span in categories_span:
        #     # Получаем и распечатываем текст каждого элемента
        #     text = await category_span.inner_text()
        #     print(text)

        # subcategories = await page.query_selector_all(
        #     "xpath=//div[@class='analizes-list-body']//*[contains(@class, 'analizes-list-item')]")
        # for subcategory in subcategories:
        #     # Выполнить действия с подкатегориями, например, клик
        #     await subcategory.click()

        # while True:
        #     # Проверяем, видим ли элемент
        #     is_visible = await page.is_visible('xpath=//span[@class="an-li-acn-icon"]')
        #     if is_visible:
        #         # Если элемент видим, кликаем по нему
        #         await page.click('xpath=//span[@class="an-li-acn-icon"]')
        #         await asyncio.sleep(0.5)  # небольшая задержка между кликами
        #     else:
        #         page_content = await page.content()
        #
        #         # Сохраняем содержимое страницы в файл
        #         with open("page_content.html", "w", encoding="utf-8") as file:
        #             file.write(page_content)
        #         break
        #         # Получаем HTML содержимое страницы
        #         page_content = await page.content()
        #         heandler = ['test_name', 'term_text', 'data_sr_id', 'data_service_id', 'category', 'price']
        #         with open('output.csv', 'w', newline='', encoding='utf-8') as file:
        #             writer = csv.writer(file, delimiter=";")
        #             writer.writerow(heandler)  # Записываем заголовки только один раз
        #             soup = BeautifulSoup(page_content, "lxml")
        #             table_results = soup.find('div', attrs={'class': 'results results-analyzes'})
        #
        #             for div in table_results.find_all('div', attrs={'class': 'result'}):
        #                 test_name = div.find('a').get_text(strip=True)
        #                 data_sr_id = div.find('div', attrs={'class': 'cell__value open-research-detail'}).get(
        #                     'data-sr-id')
        #                 data_service_id = div.find('div', attrs={'class': 'cell__value open-research-detail'}).get(
        #                     'data-service-id')
        #                 category = div.find('div', attrs={'class': 'cell__value open-research-detail'}).find('div',
        #                                                                                                      attrs={
        #                                                                                                          'class': 'cell__label'}).get_text(
        #                     strip=True)
        #                 term_div = div.find_all('div', attrs={'class': 'result__info'})
        #                 if len(term_div) > 1 and term_div[1].div:
        #                     term = term_div[1].div.find('div', attrs={'class': 'cell__value'})
        #                     term_text = term.get_text(strip=True) if term else 'Unknown Term'
        #                 else:
        #                     term_text = None
        #                 price_div = div.find('div', attrs={'class': 'discount-analyzes'})
        #                 if price_div and price_div.find('span'):
        #                     price = price_div.find('span').get_text(strip=True)
        #                 else:
        #                     price = None
        #                 values = [test_name, term_text, data_sr_id, data_service_id, category, price]
        #                 writer.writerow(values)
        #         break

        await browser.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

# from bs4 import BeautifulSoup
# import csv
# import glob
# import re
# import requests
# import json
# import cloudscraper
# import os
# import time


# def parsing():
#     file = "planeta.html"
#     with open(file, encoding="utf-8") as file:
#         src = file.read()
#
#     # Используйте BeautifulSoup для парсинга HTML
#     soup = BeautifulSoup(src, 'lxml')
#     table = soup.find('div', attrs={'id': 'analizes-list'})
#     regex_cart = re.compile('analizes-list-item analizes-list-item-.*')
#     categoty = table.find_all('div', attrs={'class': regex_cart})
#     for i in categoty:
#         name_category = i.find('div', attrs={'class': 'analizes-list-title click_pages js-price'}).get_text(strip=True)
#         categoty_id = i.find('div', attrs={'class': 'analizes-list-title click_pages js-price'}).get('data-category')
#         print(categoty_id)
#
#
# if __name__ == '__main__':
#     parsing()
