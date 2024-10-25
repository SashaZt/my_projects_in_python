import asyncio
import random
from pathlib import Path
from playwright.async_api import async_playwright
import pandas as pd
from configuration.logger_setup import logger
import aiofiles
import os
from bs4 import BeautifulSoup
import re

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

file_proxy = configuration_directory / "roman.txt"


# Функция загрузки списка прокси
def load_proxies():
    if os.path.exists(file_proxy):
        with open(file_proxy, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file]
        logger.info(f"Загружено {len(proxies)} прокси.")
        return proxies
    else:
        logger.warning(
            "Файл с прокси не найден. Работа будет выполнена локально без прокси."
        )
        return []


# Функция для парсинга прокси
def parse_proxy(proxy):
    if "@" in proxy:
        protocol, rest = proxy.split("://", 1)
        credentials, server = rest.split("@", 1)
        username, password = credentials.split(":", 1)
        return {
            "server": f"{protocol}://{server}",
            "username": username,
            "password": password,
        }
    else:
        return {"server": f"http://{proxy}"}


# # Асинхронная функция для сохранения HTML и получения ссылок по XPath
# async def single_html_one(url):
#     proxies = load_proxies()
#     proxy = random.choice(proxies) if proxies else None
#     if not proxies:
#         logger.info("Прокси не найдено, работа будет выполнена локально.")
#     try:
#         proxy_config = parse_proxy(proxy) if proxy else None
#         async with async_playwright() as p:
#             browser = (
#                 await p.chromium.launch(proxy=proxy_config, headless=False)
#                 if proxy
#                 else await p.chromium.launch(headless=False)
#             )
#             context = await browser.new_context(accept_downloads=True)
#             page = await context.new_page()

#             # Отключаем медиа
#             await page.route(
#                 "**/*",
#                 lambda route: (
#                     route.abort()
#                     if route.request.resource_type in ["image", "media"]
#                     else route.continue_()
#                 ),
#             )
#             # Переход на страницу и ожидание полной загрузки
#             await page.goto(url, timeout=60000, wait_until="networkidle")
#             # Пауза на 5 секунд
#             await asyncio.sleep(5)
#             # Поиск элемента с нужными классами
#             element = await page.query_selector(
#                 "a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active"
#             )
#             page_number = None
#             if element:
#                 # Извлекаем текст из элемента
#                 element_text = await element.inner_text()

#                 # Преобразуем текст и сохраняем в переменную page
#                 page_number_raw = element_text.strip().replace(" ", "_").lower()
#                 page_number = f"page_{page_number_raw.split('_')[-1]}"

#             content = await page.content()
#             html_file_path = html_files_directory / f"0{page_number}.html"
#             with open(html_file_path, "w", encoding="utf-8") as f:
#                 f.write(content)

#             # Цикл для нажатия на кнопку "Next Page", пока она есть на странице
#             while True:
#                 next_button = await page.query_selector(
#                     "a.ui-paginator-next.ui-state-default.ui-corner-all"
#                 )

#                 if next_button:
#                     # Нажимаем на кнопку "Next Page"
#                     await next_button.click()

#                     # Пауза, чтобы подождать загрузку новой страницы
#                     await asyncio.sleep(2)
#                     # Поиск элемента с нужными классами
#                     element = await page.query_selector(
#                         "a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active"
#                     )
#                     page_number = None
#                     if element:
#                         # Извлекаем текст из элемента
#                         element_text = await element.inner_text()

#                         # Преобразуем текст и сохраняем в переменную page
#                         page_number_raw = element_text.strip().replace(" ", "_").lower()
#                         page_number = f"page_{page_number_raw.split('_')[-1]}"

#                     content = await page.content()
#                     html_file_path = html_files_directory / f"0{page_number}.html"
#                     with open(html_file_path, "w", encoding="utf-8") as f:
#                         f.write(content)

#         await context.close()
#         await browser.close()
#     except Exception as e:
#         logger.error(f"Ошибка при обработке URL: {e}")


async def single_html_one(url):
    proxies = load_proxies()
    proxy = random.choice(proxies) if proxies else None
    if not proxies:
        logger.info("Прокси не найдено, работа будет выполнена локально.")
    try:
        proxy_config = parse_proxy(proxy) if proxy else None
        async with async_playwright() as p:
            browser = (
                await p.chromium.launch(proxy=proxy_config, headless=False)
                if proxy
                else await p.chromium.launch(headless=False)
            )
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            # Отключаем медиа
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type in ["image", "media"]
                    else route.continue_()
                ),
            )
            # Переход на страницу и ожидание полной загрузки
            await page.goto(url, timeout=60000, wait_until="networkidle")
            # Ждем, пока появится активный элемент пагинации, чтобы страница полностью загрузилась
            await page.wait_for_selector(
                "a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active"
            )
            await process_page(page)

            # Цикл для нажатия на кнопку "Next Page", пока не найдется нужный элемент
            attempts = 0
            max_attempts = 5

            while attempts < max_attempts:
                next_button = await page.query_selector(
                    "a.ui-paginator-next.ui-state-default.ui-corner-all"
                )
                if not next_button:
                    logger.warning(
                        "Кнопка 'Next Page' не найдена. Попытка {}/{}.".format(
                            attempts + 1, max_attempts
                        )
                    )
                    attempts += 1
                    await asyncio.sleep(2)
                    continue

                # Получаем текущий номер страницы перед переходом
                current_page_number = await page.query_selector(
                    "a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active"
                )
                current_page_number_text = (
                    await current_page_number.inner_text()
                    if current_page_number
                    else None
                )

                if not current_page_number_text:
                    logger.error(
                        "Не удалось получить текущий номер страницы. Попытка {}/{}.".format(
                            attempts + 1, max_attempts
                        )
                    )
                    attempts += 1
                    await asyncio.sleep(2)
                    continue

                logger.info(f"Текущая страница: {current_page_number_text}")

                # Нажимаем на кнопку "Next Page"
                await next_button.click()
                logger.info("Нажата кнопка 'Next Page'.")

                # Небольшая пауза для гарантированной подгрузки контента, если необходимо
                await asyncio.sleep(2)

                # Ждем, пока номер страницы изменится
                try:
                    await page.wait_for_function(
                        f"""
                        () => {{
                            const activePage = document.querySelector('a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active');
                            return activePage && activePage.innerText !== '{current_page_number_text}';
                        }}
                        """,
                        timeout=10000,  # Время ожидания 10 секунд
                    )
                    logger.info("Номер страницы изменился, переход успешно выполнен.")
                    attempts = 0  # Сбрасываем счетчик попыток, так как переход успешен
                except Exception as e:
                    attempts += 1
                    logger.warning(
                        f"Не удалось дождаться изменения номера страницы (попытка {attempts}/{max_attempts}): {str(e)}. Возможно, загрузка не произошла."
                    )
                    await asyncio.sleep(2)
                    continue

                # Обрабатываем текущую страницу
                await process_page(page)

            # Если максимальное количество попыток исчерпано
            if attempts == max_attempts:
                logger.error(
                    f"Максимальное количество попыток ({max_attempts}) достигнуто. Остановка выполнения."
                )

                # try:
                #     # Ждем появления целевого элемента на странице (Page 700)
                #     target_element = await page.wait_for_selector(
                #         'a.ui-paginator-page.ui-state-default.ui-corner-all[aria-label="Page 700"]',
                #         timeout=5000,
                #     )
                #     if target_element:
                #         logger.info("Элемент с текстом 'Page 700' найден.")
                #         # Переходим к новому этапу, чтобы дождаться, пока элемент пропадет
                #         while True:
                #             # Ищем кнопку "Next Page"
                #             next_button = await page.query_selector(
                #                 "a.ui-paginator-next.ui-state-default.ui-corner-all"
                #             )
                #             if not next_button:
                #                 logger.warning(
                #                     "Кнопка 'Next Page' не найдена. Останов остановлен."
                #                 )
                #                 break

                #             # Нажимаем на кнопку "Next Page" и ждем загрузки страницы
                #             await next_button.click()
                #             await page.wait_for_load_state("networkidle")

                #             # Проверяем, пропал ли целевой элемент
                #             target_element = await page.query_selector(
                #                 'a.ui-paginator-page.ui-state-default.ui-corner-all[aria-label="Page 700"]'
                #             )
                #             if not target_element:
                #                 logger.info(
                #                     "Элемент с текстом 'Page 700' больше не отображается."
                #                 )
                #                 break

                #             # Обрабатываем текущую страницу
                #             await process_page(page)

                #         # Когда элемент пропал, выходим из первого цикла
                #         break
                # except:
                #     # Если нужный элемент не найден в течение 5 секунд, продолжаем с кнопкой "Next Page"
                #     pass

                # Ищем кнопку "Next Page"

        await context.close()
        await browser.close()
    except Exception as e:
        logger.error(f"Ошибка при обработке URL: {e}")


async def process_page(page):
    try:
        # Поиск элемента с нужными классами
        element = await page.query_selector(
            "a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active"
        )
        page_number = None
        if element:
            element_text = await element.inner_text()
            page_number_raw = element_text.strip().replace(" ", "_").lower()
            page_number = f"page_{page_number_raw.split('_')[-1]}"

        if page_number:
            content = await page.content()
            html_file_path = html_files_directory / f"0{page_number}.html"
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            logger.warning("Не удалось определить номер страницы.")
    except Exception as e:
        logger.error(f"Ошибка при обработке страницы: {e}")


def parsing_page():
    # Множество для хранения уникальных itm_value
    all_data = []
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_files_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content: str = file.read()
            # Создать объект BeautifulSoup
            serial_number = None
            ad_number = None
            name_of_purchase = None
            winners_names = None
            lot_number = None
            contract_price = None
            contract_number = None
            contract_signing_date = None
            soup = BeautifulSoup(content, "lxml")
            table_ad = soup.find(
                "tbody", attrs={"class": "ui-datatable-data ui-widget-content"}
            )

            if table_ad:
                all_ad = table_ad.find_all(
                    "tr", class_=re.compile(r"ui-widget-content ui-datatable*")
                )
                if all_ad:
                    for ad in all_ad:
                        # Находим все ячейки в строке
                        td_elements = ad.find_all("td")

                        # Извлекаем данные
                        serial_number = (
                            td_elements[0].get_text(strip=True).replace("№", "").strip()
                        )
                        ad_number = (
                            td_elements[1]
                            .get_text(strip=True)
                            .replace("Номер объявления", "")
                            .strip()
                        )
                        name_of_purchase = (
                            td_elements[2]
                            .get_text(strip=True)
                            .replace("Наименование закупки", "")
                            .strip()
                        )
                        winners_names = (
                            td_elements[3]
                            .get_text(strip=True)
                            .replace("Наименования победителя", "")
                            .strip()
                        )
                        lot_number = (
                            td_elements[4]
                            .get_text(" ", strip=True)
                            .replace("Номер лота", "")
                            .strip()
                        )
                        contract_price = (
                            td_elements[6]
                            .get_text(" ", strip=True)
                            .replace("Цена предложенная участником", "")
                            .replace("\xa0", " ")
                            .strip()
                        )

                        texts = [
                            text.strip()
                            for text in td_elements[6].find_all(
                                string=True, recursive=False
                            )
                        ]
                        contract_price = ", ".join(
                            text.replace("\xa0", " ") for text in texts
                        )
                        contract_price = contract_price.lstrip(", ")
                        # Разбиваем текст по "<br><br>" и объединяем через запятую, если значений больше одного
                        # prices = [
                        #     price.strip()
                        #     for price in contract_price.split("  ")
                        #     if price
                        # ]

                        # # Объединяем значения через запятую
                        # contract_price_cleaned = ", ".join(prices)
                        # logger.info(price)
                        contract_number = (
                            td_elements[8]
                            .get_text(strip=True)
                            .replace("Номер контракта", "")
                            .strip()
                        )
                        contract_signing_date = (
                            td_elements[9]
                            .get_text(strip=True)
                            .replace("Дата подписания контракта", "")
                            .strip()
                        )

                        datas = {
                            "№": serial_number,
                            "Номер объявления": ad_number,
                            "Наименование закупки": name_of_purchase,
                            "Наименования победителя": winners_names,
                            "Номер лота": lot_number,
                            "Цена контракта": contract_price,
                            "Номер контракта": contract_number,
                            "Дата подписания контракта": contract_signing_date,
                        }
                        all_data.append(datas)
    # logger.info(all_data)
    df = pd.DataFrame(all_data)
    df.to_excel("output.xlsx", index=False)


# save_data_to_json(all_data)
#             phone_number_tag = div_element.find("b")
#             if phone_number_tag:
#                 phone_number = phone_number_tag.get_text(strip=True)
#                 phone_number = phone_number.replace(" ", "").replace("\n", "")
#                 phone_number = f"+49{phone_number}"

#         profile_raw = soup.find("span", attrs={"class": "badge bg-warning-light"})
#         if profile_raw:
#             profile = profile_raw.get_text(strip=True)
#         img_raw = (
#             soup.find(
#                 "div", attrs={"class": "media mb-1 pb-md-1 align-items-stretch"}
#             )
#             .find("a")
#             .get("href")
#         )

#         img = f"https:{img_raw}"
#         doctor_specializations_raw = soup.find(
#             "span", attrs={"data-test-id": "doctor-specializations"}
#         )
#         if doctor_specializations_raw:
#             doctor_specializations = " ".join(
#                 doctor_specializations_raw.get_text(strip=True).split()
#             )
#             doctor_specializations = [
#                 spec.strip() for spec in doctor_specializations.split(",")
#             ]
#         rating_raw = soup.find(
#             "u",
#             attrs={
#                 "class": "rating rating-lg unified-doctor-header-info__rating-text"
#             },
#         )
#         if rating_raw:
#             rating = rating_raw.get("data-score")
#             reviews = (
#                 rating_raw.find("span")
#                 .get_text(strip=True)
#                 .replace(" Bewertungen", "")
#             )
#         name_raw = soup.find("span", attrs={"itemprop": "name"})
#         if name_raw:
#             name = name_raw.get_text(strip=True)
#         clinic_name_raw = soup.find("div", attrs={"data-test-id": "address-info"})
#         if clinic_name_raw:
#             clinic_name = " ".join(
#                 clinic_name_raw.find("a").get_text(strip=True).split()
#             )
#             adress_raw = clinic_name_raw.find(
#                 "span", attrs={"itemprop": "streetAddress"}
#             )
#             adress = " ".join(adress_raw.get_text(strip=True).split())
#         description_section = soup.find("section", id="about-section")
#         if description_section:
#             title_element = description_section.find(
#                 "h2", class_="h3 section-header mb-1-5"
#             )
#             title = title_element.get_text(strip=True) if title_element else ""

#             herzlich_willkommen_element = description_section.find_all(
#                 "div", class_="about-description"
#             )
#             herzlich_willkommen_text = " ".join(
#                 [
#                     " ".join(herz.get_text(separator=" ", strip=True).split())
#                     for herz in herzlich_willkommen_element
#                 ]
#             )

#             description = {
#                 "title": title,
#                 "Herzlich willkommen": herzlich_willkommen_text,
#             }
#         accepted_insurances_raw = soup.find(
#             "div", attrs={"data-test-id": "insurance-info"}
#         )
#         if accepted_insurances_raw:
#             accepted_insurances = accepted_insurances_raw.find_all(
#                 "a", class_="text-muted"
#             )
#             accepted_insurances = [
#                 link.get_text(strip=True) for link in accepted_insurances
#             ]
#         # Извлечение информации о сервисах и их описаниях
#         services_section = soup.find("section", id="profile-pricing")
#         services = []
#         if services_section:
#             service_elements = services_section.find_all(
#                 "div", attrs={"data-test-id": "profile-pricing-list-details"}
#             )
#             for service_element in service_elements:
#                 service_name_element = service_element.find_previous_sibling(
#                     "div", attrs={"data-test-id": "profile-pricing-list-element"}
#                 )
#                 service_name = (
#                     service_name_element.find(
#                         "p", itemprop="availableService"
#                     ).get_text(strip=True)
#                     if service_name_element
#                     else ""
#                 )

#                 service_description_element = service_element.find(
#                     "p",
#                     attrs={"data-test-id": "profile-pricing-element-description"},
#                 )
#                 service_description = (
#                     " ".join(
#                         service_description_element.get_text(strip=True).split()
#                     )
#                     if service_description_element
#                     else ""
#                 )

#                 if service_name and service_description:
#                     services.append([service_name, service_description])
#         opening_hours_element = soup.find(
#             "div", attrs={"data-id": re.compile(r"^opening-hours-.*")}
#         )
#         opening_hours = []
#         if opening_hours_element:
#             rows = opening_hours_element.find_all(
#                 "div", class_=re.compile(r"row pb-0-5.*")
#             )
#             days_map = {
#                 "Montag": 0,
#                 "Dienstag": 1,
#                 "Mittwoch": 2,
#                 "Donnerstag": 3,
#                 "Freitag": 4,
#                 "Samstag": 5,
#                 "Sonntag": 6,
#             }
#             for row in rows:
#                 day_name_element = row.find("div", class_="col-4 col-md-4")
#                 if day_name_element:
#                     day_name = day_name_element.get_text(strip=True)
#                     day = days_map.get(day_name)
#                     if day is not None:
#                         ranges = []
#                         time_elements = row.find_all("div", class_="col-4 col-md-3")
#                         for time_element in time_elements:
#                             times = (
#                                 time_element.get_text(strip=True)
#                                 .replace(" ", "")
#                                 .replace("\n", "")
#                                 .split("-")
#                             )
#                             if len(times) == 2:
#                                 ranges.append([times[0], times[1]])
#                         opening_hours.append({"day": day, "ranges": ranges})
#         datas = {
#             "phone_number": phone_number,
#             "profile": profile,
#             "img": img,
#             "doctor_specializations": doctor_specializations,
#             "rating": rating,
#             "reviews": reviews,
#             "name": name,
#             "clinic_name": clinic_name,
#             "adress": adress,
#             "description": description,
#             "accepted_insurances": accepted_insurances,
#             "services": services,
#             "opening_hours": opening_hours,
#         }
#         all_data.append(datas)

# save_data_to_json(all_data)


# Функция для выполнения основной логики
def main():
    url = "http://zakupki.gov.kg/popp/view/order/winners.xhtml"
    asyncio.run(single_html_one(url))


if __name__ == "__main__":
    # main()
    parsing_page()
