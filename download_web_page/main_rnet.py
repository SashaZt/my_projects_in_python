import asyncio
import json

from config.logger import logger
from rnet import Client, Impersonate

cookies = {
    "userId": "443137514687636968563266902265495",
    "exchange": "UAH",
    "__utmzzses": "1",
    "lng": "en",
    "region": "ukraine",
    "cf_clearance": "iKvu5x7EHH3s9xxz6JcDw4yIDQVmcz7h2XAKWWbysU4-1751552749-1.2.1.1-hNsAMMC4Dcuu6X9Qp6dai.lASk8eNCUAJcqmRE7VSmo3iHOBcd1pmw_Nz9vIoE9X7IpMVXj_7rtYCl3RDciMji7JNYSmmQz6VdFwWmX3SY8CKivTT.rYxdiK_VsLJWtf3T_mbhRtWOLTxUhwdlRarJKomwDQvkPbmQVVEyTQVVV7KbB5Qk3l8Z3dRfV.A9izCCaows_mvqgobGrobrGqv8jHxHnObl7wax5EZsQpZ0s",
    "cconsent": "1",
    "scm": "d.ukraine.9da773de45261ddb.345d06a53c29e7be70cc6dbfb4c18758a357258efa7bdf87c71d25e72c0bb59f",
    "PHPSESSID_": "t2j9rp26187veoercjgdcgrc58",
}

headers = {
    "accept": "*/*",
    "accept-language": "en",
    "baggage": "sentry-environment=production,sentry-release=eneba%3Awww%401.3109.2,sentry-public_key=0857afeb74f643e19d8c7aec931404b3,sentry-trace_id=ca536fe4ee21453897627fb0d224ed73,sentry-sample_rate=0,sentry-sampled=false",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://www.eneba.com",
    "priority": "u=1, i",
    "referer": "https://www.eneba.com/store/games?drms[]=xbox&enb_campaign=Homepage&enb_content=Main%2520Categories%2520Navigation&enb_medium=link&enb_source=https%253A%252F%252Fwww.eneba.com%252F&enb_term=Games&page=2&rangeTo=1000&regions[]=argentina&regions[]=turkey&regions[]=united_states&regions[]=europe&regions[]=global&types[]=game",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-gpc": "1",
    "sentry-trace": "ca536fe4ee21453897627fb0d224ed73-b57346e6e5111089-0",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "x-version": "1.3109.2",
    # 'cookie': 'userId=443137514687636968563266902265495; exchange=UAH; __utmzzses=1; lng=en; region=ukraine; cf_clearance=iKvu5x7EHH3s9xxz6JcDw4yIDQVmcz7h2XAKWWbysU4-1751552749-1.2.1.1-hNsAMMC4Dcuu6X9Qp6dai.lASk8eNCUAJcqmRE7VSmo3iHOBcd1pmw_Nz9vIoE9X7IpMVXj_7rtYCl3RDciMji7JNYSmmQz6VdFwWmX3SY8CKivTT.rYxdiK_VsLJWtf3T_mbhRtWOLTxUhwdlRarJKomwDQvkPbmQVVEyTQVVV7KbB5Qk3l8Z3dRfV.A9izCCaows_mvqgobGrobrGqv8jHxHnObl7wax5EZsQpZ0s; cconsent=1; scm=d.ukraine.9da773de45261ddb.345d06a53c29e7be70cc6dbfb4c18758a357258efa7bdf87c71d25e72c0bb59f; PHPSESSID_=t2j9rp26187veoercjgdcgrc58',
}

json_data = {
    "operationName": "Store",
    "variables": {
        "currency": "UAH",
        "context": {
            "country": "UA",
            "region": "ukraine",
            "language": "en",
        },
        "searchType": "DEFAULT",
        "types": [
            "game",
        ],
        "drms": [
            "xbox",
        ],
        "regions": [
            "argentina",
            "turkey",
            "united_states",
            "europe",
            "global",
        ],
        "sortBy": "POPULARITY_DESC",
        "after": "YXJyYXljb25uZWN0aW9uOjE5",
        "first": 20,
        "price": {
            "to": 100000,
            "currency": "UAH",
        },
        "url": "/store/games",
        "redirectUrl": "https://www.eneba.com/store/games",
    },
    "extensions": {
        "persistedQuery": {
            "version": 1,
            "sha256Hash": "e7c4cb284593ba8790a73238ee99c8b3cceb6dae6a3bd6a3eb46de758bab688e_fa9d4ba78292d78e2783bcbfcafd66f124a700122195de5fb927b7244800cf5a3e299cb9abf45322afaac142ce79f9f89d4447d0d908f83f9ff19f79be55f40e",
        },
    },
}


async def response_methods():
    client = Client(impersonate=Impersonate.Chrome120)

    response = await client.get(
        "https://www.eneba.com/graphql/",
        cookies=cookies,
        headers=headers,
        json=json_data,
    )

    logger.info(f"Status Code: {response.status_code}")
    try:

        text_content = await response.text()
        logger.info(text_content)
        logger.info(json.dumps(text_content))
        return text_content
    except Exception as e:
        logger.error(f"❌ response.text() ошибка: {e}")

    return None


async def main():

    content = await response_methods()
    # logger.info(content)


if __name__ == "__main__":
    asyncio.run(main())
# """
# Рабочий код что выше
# """
# import asyncio
# import json
# import urllib.parse
# from urllib.parse import unquote, urlencode

# from config.logger import logger
# from rnet import Client, Impersonate
# from selectolax.parser import HTMLParser

# HEADERS = {
#     "accept": "application/json, text/plain, */*",
#     "accept-language": "ru,en;q=0.9,uk;q=0.8",
#     "cache-control": "max-age=0",
#     "content-type": "application/x-www-form-urlencoded",
#     "dnt": "1",
#     "origin": "https://www.tikleap.com",
#     "priority": "u=0, i",
#     "referer": "https://www.tikleap.com",
#     "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": '"macOS"',
#     "sec-fetch-dest": "document",
#     "sec-fetch-mode": "navigate",
#     "sec-fetch-site": "same-origin",
#     "sec-fetch-user": "?1",
#     "sec-gpc": "1",
#     "upgrade-insecure-requests": "1",
#     "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
# }


# def update_cookies_from_response(response, cookie_dict):
#     """Обновляет словарь кук из ответа"""
#     if hasattr(response, "cookies") and response.cookies:
#         for cookie in response.cookies:
#             cookie_dict[cookie.name] = cookie.value
#             logger.info(f"Обновлена кука: {cookie.name}")
#     return cookie_dict


# async def login_flow():
#     """Полный процесс авторизации точно по curl командам"""
#     session = Client(
#         impersonate=Impersonate.Chrome120,
#         user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
#     )

#     try:
#         cookie_dict = {}

#         # Шаг 1: GET /login (первый раз БЕЗ кук)
#         logger.info("1. Загружаем страницу логина...")
#         login_page_response = await session.get("https://www.tikleap.com/login")
#         logger.info(f"Статус страницы логина: {login_page_response.status_code}")

#         # Извлекаем куки из первого ответа
#         cookie_dict = update_cookies_from_response(login_page_response, cookie_dict)
#         logger.info(f"Получены начальные куки: {list(cookie_dict.keys())}")

#         # Извлекаем CSRF токен из meta тега
#         html_text = await login_page_response.text()
#         parser = HTMLParser(html_text)
#         # csrf_meta = parser.css_first('meta[name="csrf-token"]')

#         # if not csrf_meta:
#         #     logger.error("CSRF токен не найден на странице")
#         #     return None

#         # csrf_token = csrf_meta.attributes.get("content")

#         csrf_meta = parser.css_first('meta[name="csrf-token"]')
#         csrf_token = csrf_meta.attributes.get("content")
#         logger.info(f"CSRF токен извлечен: {csrf_token}")

#         # Шаг 2: POST /login (с куками и CSRF токеном)
#         logger.info("2. Выполняем POST авторизацию...")

#         # Извлекаем и декодируем X-XSRF-TOKEN из куки для заголовка
#         xsrf_header_value = None
#         if "XSRF-TOKEN" in cookie_dict:
#             xsrf_header_value = unquote(cookie_dict["XSRF-TOKEN"])
#             logger.info(f"X-XSRF-TOKEN (из куки) = {xsrf_header_value}")
#         else:
#             logger.warning("XSRF-TOKEN не найден в cookies")

#         # POST данные с _token из meta тега (в теле запроса)
#         data_raw = urlencode(
#             {
#                 "_token": csrf_token,
#                 "email": "37200@starlivemail.com",
#                 "password": "bfnsa232@1!dsA",
#             }
#         )
#         logger.info(data_raw)
#         # Заголовки с X-XSRF-TOKEN (в заголовках)
#         post_headers = HEADERS.copy()
#         # if xsrf_header_value:
#         #     post_headers["X-XSRF-TOKEN"] = (
#         #         xsrf_header_value  # X-XSRF-TOKEN в заголовках
#         #     )

#         logger.info(f"POST с куками: {list(cookie_dict.keys())}")
#         logger.info(f"_token (в теле) = {csrf_token}")
#         logger.info(f"X-XSRF-TOKEN (в заголовке) = {xsrf_header_value}")
#         logger.info(
#             f"XSRF-TOKEN (в куки) = {cookie_dict.get('XSRF-TOKEN', 'НЕТ')[:50]}..."
#         )

#         # POST запрос с тремя типами CSRF токенов:
#         # 1. _token в data (теле запроса)
#         # 2. X-XSRF-TOKEN в headers (заголовках)
#         # 3. XSRF-TOKEN автоматически в cookies
#         login_response = await session.post(
#             "https://www.tikleap.com/login",
#             headers=post_headers,  # содержит X-XSRF-TOKEN
#             data=data_raw,  # содержит _token
#             cookies=cookie_dict,  # содержит XSRF-TOKEN
#         )

#         logger.info(f"Статус POST авторизации: {login_response.status_code}")

#         # Обновляем куки из ответа POST
#         cookie_dict = update_cookies_from_response(login_response, cookie_dict)

#         # Логируем заголовки ответа для диагностики
#         logger.info("Заголовки ответа POST авторизации:")
#         for name, value in login_response.headers.items():
#             if isinstance(name, bytes):
#                 name = name.decode()
#             if isinstance(value, bytes):
#                 value = value.decode()
#             logger.info(f"  {name}: {value}")
#         if login_response.status_code == 302:
#             location = login_response.headers.get("location", "")
#             if "/login" in location:
#                 # Загружаем HTML редиректа
#                 failed_page = await session.get(location, cookies=cookie_dict)
#                 html = await failed_page.text()
#                 with open("login_failed.html", "w", encoding="utf-8") as f:
#                     f.write(html)
#                 logger.error("❌ Ошибка входа. Сохранен HTML login_failed.html")
#         # Шаг 3: Обрабатываем результат авторизации
#         if str(login_response.status_code) == "302":
#             logger.info("3. ✅ Получен редирект - авторизация успешна!")

#             redirect_url = (
#                 login_response.headers.get("location")
#                 or login_response.headers.get("Location")
#                 or "/"
#             )
#             if isinstance(redirect_url, bytes):
#                 redirect_url = redirect_url.decode()
#             if redirect_url.startswith("/"):
#                 redirect_url = "https://www.tikleap.com" + redirect_url

#             logger.info(f"Редирект на: {redirect_url}")

#             # Проверяем куда идет редирект
#             if "/login" in redirect_url:
#                 logger.info(f"Загружаем страницу ошибки: {redirect_url}")
#                 failed_page = await session.get(redirect_url, cookies=cookie_dict)
#                 html = await failed_page.text()
#                 with open("login_failed.html", "w", encoding="utf-8") as f:
#                     f.write(html)
#                 logger.error("❌ Ошибка входа. Сохранен HTML в login_failed.html")
#                 logger.error("❌ Редирект обратно на login - авторизация НЕ ПРОШЛА!")
#                 return None

#             # Шаг 4: GET главная страница (с обновленными куками)
#             logger.info("4. Загружаем главную страницу...")

#             main_headers = {
#                 "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
#                 "accept-language": "ru,en;q=0.9,uk;q=0.8",
#                 "cache-control": "max-age=0",
#                 "dnt": "1",
#                 "priority": "u=0, i",
#                 "Origin": "https://www.tikleap.com",
#                 "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
#                 "sec-ch-ua-mobile": "?0",
#                 "sec-ch-ua-platform": '"macOS"',
#                 "sec-fetch-dest": "document",
#                 "sec-fetch-mode": "navigate",
#                 "sec-fetch-site": "same-origin",
#                 "sec-fetch-user": "?1",
#                 "sec-gpc": "1",
#                 "upgrade-insecure-requests": "1",
#                 "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
#             }

#             logger.info(f"GET главная с куками: {list(cookie_dict.keys())}")
#             main_response = await session.get(
#                 "https://www.tikleap.com/",
#                 headers=main_headers,
#                 cookies=cookie_dict,
#             )
#             logger.info(f"Статус главной страницы: {main_response.status_code}")

#             # Обновляем куки с главной страницы
#             cookie_dict = update_cookies_from_response(main_response, cookie_dict)

#         elif str(login_response.status_code) == "200":
#             logger.info("3. Авторизация завершена без редиректа")
#         else:
#             logger.error(
#                 f"❌ Неожиданный статус авторизации: {login_response.status_code}"
#             )
#             return None
#         # Шаг 6: Сохраняем финальные куки
#         logger.info("6. Сохраняем финальные куки...")
#         logger.info("Финальные куки:")
#         for name, value in cookie_dict.items():
#             logger.info(f"  {name}: {value[:50]}...")

#         with open("session_cookies.json", "w", encoding="utf-8") as f:
#             json.dump(cookie_dict, f, indent=4, ensure_ascii=False)

#         logger.info(f"Куки сохранены в файл. Всего: {len(cookie_dict)}")

#         # Шаг 7: Тестируем API запрос
#         logger.info("7. Тестируем API запрос...")
#         success = await test_api_request(session, cookie_dict)

#         if success:
#             logger.info("🎉 ВСЁ РАБОТАЕТ! Авторизация и API успешны!")
#         else:
#             logger.error("❌ API запрос не работает")

#         return session

#     except Exception as e:
#         logger.error(f"Ошибка в login_flow: {e}")
#         import traceback

#         logger.error(traceback.format_exc())
#         return None


# async def test_api_request(session, cookie_dict):
#     """Тестируем API запрос с финальными куками"""
#     url = "https://www.tikleap.com/country-load-more/kz/2"

#     headers_api = {
#         "accept": "*/*",
#         "accept-language": "ru,en;q=0.9,uk;q=0.8",
#         "dnt": "1",
#         "priority": "u=1, i",
#         "referer": "https://www.tikleap.com/country/kz",
#         "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-platform": '"macOS"',
#         "sec-fetch-dest": "empty",
#         "sec-fetch-mode": "cors",
#         "sec-fetch-site": "same-origin",
#         "sec-gpc": "1",
#         "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
#         "x-requested-with": "XMLHttpRequest",
#     }

#     try:
#         logger.info(f"API запрос с куками: {list(cookie_dict.keys())}")

#         # Делаем API запрос с финальными куками
#         response = await session.get(url, headers=headers_api, cookies=cookie_dict)
#         logger.info(f"Статус API запроса: {response.status_code}")

#         if response.status_code == 200:
#             text = await response.text()
#             logger.info(f"✅ API работает! Получен контент: {len(text)} символов")

#             # После успешного API запроса обновляем куки (они могли измениться!)
#             cookie_dict = update_cookies_from_response(response, cookie_dict)

#             # Сохраняем обновленные куки
#             with open("session_cookies.json", "w", encoding="utf-8") as f:
#                 json.dump(cookie_dict, f, indent=4, ensure_ascii=False)
#             logger.info("Куки обновлены после API запроса")

#             return True
#         else:
#             logger.error(f"❌ API запрос неудачен: {response.status_code}")
#             return False

#     except Exception as e:
#         logger.error(f"❌ Ошибка API запроса: {e}")
#         return False


# async def main():
#     """Главная функция"""
#     logger.info("🚀 Запуск процесса авторизации на TikLeap")

#     session = await login_flow()

#     if session:
#         logger.info("🎉 Авторизация завершена успешно!")
#         logger.info("Куки сохранены в session_cookies.json")
#     else:
#         logger.error("❌ Авторизация не удалась")


# if __name__ == "__main__":
#     asyncio.run(main())
