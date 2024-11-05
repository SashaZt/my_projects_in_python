# import requests
# from bs4 import BeautifulSoup


# def get_html_proxy():
#     url = 'https://hideee.name/proxy-list/'
#     # Укажите ваши cookies и headers
#     cookies = {
#         't': '424620214',
#     }

#     headers = {
#         'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#         'accept-language': 'ru,en;q=0.9,uk;q=0.8',
#         'cache-control': 'no-cache',
#         # 'cookie': 't=424620214',
#         'dnt': '1',
#         'pragma': 'no-cache',
#         'priority': 'u=0, i',
#         'referer': 'https://hideee.name/proxy-list/?maxtime=100',
#         'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-platform': '"Windows"',
#         'sec-fetch-dest': 'document',
#         'sec-fetch-mode': 'navigate',
#         'sec-fetch-site': 'same-origin',
#         'sec-fetch-user': '?1',
#         'upgrade-insecure-requests': '1',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
#     }

#     proxy_list = []
#     start = 0  # начальное значение для пагинации

#     for i in range(5):  # выполняем 5 запросов
#         # Определяем параметры для первого и последующих запросов
#         params = {
#             'maxtime': '100',
#             'type': 'hs',
#             # добавляем параметр 'start' для второй страницы и далее
#             'start': start if i > 0 else None
#         }

#         # Отправляем запрос к серверу
#         response = requests.get(
#             url, params=params, cookies=cookies, headers=headers)
#         response.raise_for_status()  # проверяем, что запрос успешен

#         # Парсим содержимое HTML с помощью BeautifulSoup
#         soup = BeautifulSoup(response.text, "html.parser")
#         rows = soup.select(
#             "body > div.wrap > div.services_proxylist.services > div > div.table_block > table > tbody > tr"
#         )

#         # Извлекаем IP и порт из каждой строки таблицы
#         for row in rows:
#             ip = row.find_all("td")[0].text.strip()  # Первый <td> — IP
#             port = row.find_all("td")[1].text.strip()  # Второй <td> — порт
#             proxy = f"http://{ip}:{port}"
#             proxy_list.append(proxy)

#         start += 64  # увеличиваем смещение для следующей страницы
#     # print(len(proxy_list))
#     # Проверяем каждый прокси через httpbin
#     valid_proxies = []
#     for proxy in proxy_list:
#         proxies = {
#             "http": proxy,
#             "https": proxy,
#         }
#         try:
#             # Отправляем запрос через прокси на httpbin.org/ip
#             response = requests.get(
#                 "http://httpbin.org/ip", proxies=proxies, timeout=5)
#             response.raise_for_status()
#             origin_ip = response.json().get("origin")

#             # Проверяем, совпадает ли IP
#             if origin_ip in proxy:
#                 valid_proxies.append(proxy)
#                 print(f"{proxy} - Совпадает")
#             else:
#                 print(f"{proxy} - Не совпадает")
#         except requests.RequestException:
#             print(f"{proxy} - Ошибка соединения")

# Записываем только совпадающие прокси в файл
# with open("proxy.txt", "w") as outfile:
#     for proxy in valid_proxies:
#         outfile.write(proxy + "\n")

#     print("Файл proxy.txt успешно создан.")


# # Запуск функции
# get_html_proxy()

# Логин, пароль и порт
login = "eu3040926"
password = "ej1G3umfak"
port = 7952

# Читаем IP-адреса из input.txt
with open("input.txt", "r") as infile:
    # Формируем прокси в нужном формате
    formatted_proxies = [
        f"http://{login}:{password}@{ip.strip()}:{port}"
        for ip in infile
    ]

# Записываем результат в proxy.txt
with open("proxy.txt", "w") as outfile:
    for proxy in formatted_proxies:
        outfile.write(proxy + "\n")

print("Файл proxy.txt успешно создан.")
