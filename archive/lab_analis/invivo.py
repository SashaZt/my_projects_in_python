import asyncio
import os
import csv
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://invivo.ua/uk/vinnickay/analyzes-and-cost/")
        await page.click('xpath=//div[@id="search__result-analyzes"]')
        await asyncio.sleep(1)
        # Цикл, который будет кликать на элемент, пока он видим
        while True:
            # Проверяем, видим ли элемент
            is_visible = await page.is_visible('xpath=//div[@class="more__btn more__btn--close"]')
            if is_visible:
                # Если элемент видим, кликаем по нему
                await page.click('xpath=//div[@class="more__btn more__btn--close"]')
                await asyncio.sleep(0.5)  # небольшая задержка между кликами
            else:
                # Получаем HTML содержимое страницы
                page_content = await page.content()
                heandler = ['test_name', 'term_text', 'data_sr_id', 'data_service_id', 'category', 'price']
                with open('output.csv', 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, delimiter=";")
                    writer.writerow(heandler)  # Записываем заголовки только один раз
                    soup = BeautifulSoup(page_content, "lxml")
                    table_results = soup.find('div', attrs={'class': 'results results-analyzes'})

                    for div in table_results.find_all('div', attrs={'class': 'result'}):
                        test_name = div.find('a').get_text(strip=True)
                        data_sr_id = div.find('div', attrs={'class': 'cell__value open-research-detail'}).get(
                            'data-sr-id')
                        data_service_id = div.find('div', attrs={'class': 'cell__value open-research-detail'}).get(
                            'data-service-id')
                        category = div.find('div', attrs={'class': 'cell__value open-research-detail'}).find('div',
                                                                                                             attrs={
                                                                                                                 'class': 'cell__label'}).get_text(
                            strip=True)
                        term_div = div.find_all('div', attrs={'class': 'result__info'})
                        if len(term_div) > 1 and term_div[1].div:
                            term = term_div[1].div.find('div', attrs={'class': 'cell__value'})
                            term_text = term.get_text(strip=True) if term else 'Unknown Term'
                        else:
                            term_text = None
                        price_div = div.find('div', attrs={'class': 'discount-analyzes'})
                        if price_div and price_div.find('span'):
                            price = price_div.find('span').get_text(strip=True)
                        else:
                            price = None
                        values = [test_name, term_text, data_sr_id, data_service_id, category, price]
                        writer.writerow(values)
                break

        await browser.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
