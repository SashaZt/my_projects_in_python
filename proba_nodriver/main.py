import asyncio

import nodriver as uc

"""
 Настраиваем аргументы браузера
        # browser_args = ["--headless=new"]

        # # Открываем браузер
        # print("Запускаем браузер с --headless=new...")
        # browser = await uc.start(browser_args=browser_args)
        # Открываем браузер
"""


# async def main():
#     browser = None
#     page = None
#     try:
#         # Настраиваем аргументы браузера открою в рабочей версии
#         browser_args = ["--headless=new"]
#         browser_args = []

#         # Открываем браузер
#         print("Запускаем браузер с --headless=new...")
#         browser = await uc.start(browser_args=browser_args)
#         # Открываем браузер
#         # browser = await uc.start(headless=False)
#         if not browser:
#             raise ValueError("Не удалось инициализировать браузер")
#         print("Браузер успешно запущен")

#         # Переходим на страницу
#         print("Переходим на страницу логина...")
#         page = await browser.get(
#             "https://easy.co.il/list/Maintenance-and-Management-Of-Buildings"
#         )
#         if not page:
#             raise ValueError("Не удалось загрузить страницу")

#         # Ждем загрузки
#         await asyncio.sleep(100)

#     except Exception as e:
#         print(f"Произошла ошибка: {str(e)}")
#     finally:
#         # Минимальная обработка закрытия
#         if page:
#             try:
#                 await page.close()
#             except:
#                 pass


# async def main():
#     browser = await uc.Browser.create(headless=False)
#     # Переход на страницу логина и выполнение входа
#     tab = await browser.get("https://optlist.ru/login#!?next=%2Fcompany%2Fnv-lab")
#     await asyncio.sleep(500)

#     email_field = await tab.select("#email")
#     if email_field:
#         await email_field.send_keys("radik.gizatullin.1976@mail.ru")
#         logger.info("Email вставлен.")

#     password_field = await tab.select("#pass")
#     if password_field:
#         await password_field.send_keys("BJVxcS")
#         logger.info("Пароль вставлен.")

#     login_button = await tab.select("button[type='submit']")
#     if login_button:
#         await login_button.click()
#         logger.info("Кнопка 'Войти' нажата.")

#     # Переход на страницу компании
#     await asyncio.sleep(10)  # Ожидание завершения логина
#     all_datas = []

#     for url in all_urls:  # Ограничено одной URL для теста
#         logger.info(url)
#         html_company = html_files_directory / f"{url.split('/')[-1]}.html"

#         if html_company.exists():
#             logger.warning(f"Файл {html_company} уже существует, пропускаем.")
#             continue  # Переходим к следующей итерации цикла

#         tab = await browser.get(url)

#         # Извлечение информации о компании
#         await asyncio.sleep(2)  # Ожидание загрузки страницы
#         # Задача 4: Найти название компании
#         company_name = None
#         company_email = None

#         try:
#             company_name_element = await tab.select(
#                 "span[itemprop='name'].header-box__title"
#             )
#             company_name = company_name_element.text if company_name_element else None
#             logger.info(
#                 f"Название компании: {company_name or 'Название компании не найдено'}"
#             )
#         except Exception as e:

#             logger.warning(f"Ошибка при получении названия компании: {e}")
#             continue

#         try:
#             # Задача 5: Найти email компании
#             email_element = await tab.select(
#                 "div.media-body a[href^='mailto:'] span[itemprop='email']"
#             )
#             company_email = email_element.text if email_element else None
#             logger.info(
#                 f"Email компании: {company_email or 'Email компании не найден'}"
#             )
#         except Exception as e:

#             logger.warning(f"Ошибка при получении email компании: {e}")
#             continue

#         html_content = await tab.get_content()
#         with open(html_company, "w", encoding="utf-8") as file:
#             file.write(html_content)
#         data = {"company_name": company_name, "company_email": company_email}
#         all_datas.append(data)
#     # logger.info(all_urls)
#     save_to_excel(all_datas)

#     # await tab.close()
#     # browser.stop()  # Остановка браузера


async def main():
    # Запускаем браузер
    browser = await uc.start()
    # Переходим по ссылке (замените на нужную)
    page = await browser.get(
        "https://easy.co.il/list/Maintenance-and-Management-Of-Buildings"
    )
    # Пауза 100 секунд
    await asyncio.sleep(100)
    # Закрываем браузер
    await browser.close()


if __name__ == "__main__":
    uc.loop().run_until_complete(main())