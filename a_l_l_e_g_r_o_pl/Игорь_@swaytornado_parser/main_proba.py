# import json

# import requests

# # URL для работы с API
# api_url = "https://async.scraperapi.com/jobs"

# # Целевой URL с уже сформированными параметрами
# target_url = (
#     "https://www.emag.ro/search-by-url"
#     "?source_id=7"
#     "&templates[]=full"
#     "&sort[popularity_v_opt]=desc"
#     "&listing_display_id=2"
#     "&page[limit]=100"
#     "&page[offset]=0"
#     "&fields[items][image_gallery][fashion][limit]=2"
#     "&fields[items][image][resized_images]=1"
#     "&fields[items][resized_images]=200x200,350x350,720x720"
#     "&fields[items][flags]=1"
#     "&fields[items][offer][buying_options]=1"
#     "&fields[items][offer][flags]=1"
#     "&fields[items][offer][bundles]=1"
#     "&fields[items][offer][gifts]=1"
#     "&fields[items][characteristics]=listing"
#     "&fields[quick_filters]=1"
#     "&search_id="
#     "&search_fraze="
#     "&search_key="
#     "&url=/televizoare/p2/c"
# )

# # Пользовательские заголовки
# headers = {
#     "accept": "application/json",
#     "accept-language": "ru,en;q=0.9,uk;q=0.8",
#     "content-type": "application/json",  # Устанавливаем Content-Type для JSON
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
# }

# # Тело запроса для ScraperAPI
# payload = {
#     "apiKey": "7757eea384bafff7726179e7855bb664",  # Ваш API-ключ
#     "url": target_url,  # Целевой URL
#     "keep_headers": True,  # Указываем, что используем свои заголовки
#     "method": "GET",  # HTTP-метод
# }

# # Отправка POST-запроса к ScraperAPI
# response = requests.post(api_url, json=payload, headers=headers)

# # Проверка ответа
# if response.status_code == 200:
#     print("Успешный запрос!")
#     print(response.json())  # JSON-ответ
# else:
#     print(f"Ошибка: {response.status_code}")
#     print(response.text)

# Рабочий
import json
import time

import requests

# URL для работы с API
api_url = "https://async.scraperapi.com/jobs"

# Целевой URL с уже сформированными параметрами
target_url = (
    "https://www.emag.ro/search-by-url"
    "?source_id=7"
    "&templates[]=full"
    "&sort[popularity_v_opt]=desc"
    "&listing_display_id=2"
    "&page[limit]=100"
    "&page[offset]=0"
    "&fields[items][image_gallery][fashion][limit]=2"
    "&fields[items][image][resized_images]=1"
    "&fields[items][resized_images]=200x200,350x350,720x720"
    "&fields[items][flags]=1"
    "&fields[items][offer][buying_options]=1"
    "&fields[items][offer][flags]=1"
    "&fields[items][offer][bundles]=1"
    "&fields[items][offer][gifts]=1"
    "&fields[items][characteristics]=listing"
    "&fields[quick_filters]=1"
    "&search_id="
    "&search_fraze="
    "&search_key="
    "&url=/televizoare/p2/c"
)

# Пользовательские заголовки
headers = {
    "accept": "application/json",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "content-type": "application/json",  # Устанавливаем Content-Type для JSON
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

# Тело запроса для ScraperAPI
payload = {
    "apiKey": "7757eea384bafff7726179e7855bb664",  # Ваш API-ключ
    "url": target_url,  # Целевой URL
    "keep_headers": True,  # Указываем, что используем свои заголовки
    "method": "GET",  # HTTP-метод
}

# Отправка POST-запроса к ScraperAPI
response = requests.post(api_url, json=payload, headers=headers)

# Проверка ответа
if response.status_code == 200:
    print(response.json())  # JSON-ответ
    print("Успешный запрос!")
max_retries = 100  # Максимальное количество проверок статуса
retry_delay = 10  # Задержка между проверками (в секундах)

for _ in range(max_retries):
    json_response = response.json()
    status_url = json_response.get("statusUrl")
    response = requests.get(url=status_url, timeout=30)
    job_status = json_response.get("status")
    if job_status == "finished":
        name_file = json_response.get("id")
        json_file = f"{name_file}.json"
        extracted_body = json_response.get("response", {}).get("body")

        if extracted_body:
            try:
                # Попытка обработать содержимое "body" как JSON
                cleaned_body = json.loads(extracted_body)

                # Сохранение результата в файл
                with open(json_file, "w", encoding="utf-8") as output_file:
                    json.dump(
                        cleaned_body,
                        output_file,
                        indent=4,
                        ensure_ascii=False,
                    )

                print(f"Результат сохранён в файл: {json_file}")

            except json.JSONDecodeError as e:
                print(f"Ошибка при декодировании JSON из 'body': {e}")
                print.error(f"Содержимое 'body': {extracted_body}")

    else:
        print("Задача ещё не завершена, повторная проверка...")
        time.sleep(retry_delay)  # Задержка перед следующим запросом

# import json

# # Path to the uploaded file
# file_path = (
#     "8cfdb6e6-dde8-4040-98d5-90f0f6be989d.json"  # Replace with the actual file path
# )

# output_path = "cleaned_body.json"  # Имя файла для сохранения результата

# try:
#     # Загрузка JSON-файла
#     with open(file_path, "r", encoding="utf-8") as file:
#         data = json.load(file)

#     # Извлечение поля "body"
#     extracted_body = data.get("response", {}).get("body", "")

#     # Попытка обработать содержимое "body" как JSON
#     if extracted_body:
#         try:
#             cleaned_body = json.loads(extracted_body)

#             # Сохранение результата в новый JSON-файл
#             with open(output_path, "w", encoding="utf-8") as output_file:
#                 json.dump(cleaned_body, output_file, indent=4, ensure_ascii=False)

#             print(f"Очищенный JSON успешно сохранён в файл: {output_path}")
#         except json.JSONDecodeError as e:
#             print(f"Ошибка при декодировании JSON из 'body': {e}")
#             print("Содержимое 'body':")
#             print(extracted_body)
#     else:
#         print("Поле 'body' пустое или отсутствует в файле.")
# except FileNotFoundError:
#     print(f"Файл не найден: {file_path}")
# except json.JSONDecodeError as e:
#     print(f"Ошибка при чтении основного JSON-файла: {e}")


# import requests

# # URL для работы с API
# api_url = "https://api.scraperapi.com"

# # Ваш API-ключ
# api_key = "7757eea384bafff7726179e7855bb664"

# # Целевой URL с уже сформированными параметрами
# target_url = (
#     "https://www.emag.ro/search-by-url"
#     "?source_id=7"
#     "&templates[]=full"
#     "&sort[popularity_v_opt]=desc"
#     "&listing_display_id=2"
#     "&page[limit]=100"
#     "&page[offset]=0"
#     "&fields[items][image_gallery][fashion][limit]=2"
#     "&fields[items][image][resized_images]=1"
#     "&fields[items][resized_images]=200x200,350x350,720x720"
#     "&fields[items][flags]=1"
#     "&fields[items][offer][buying_options]=1"
#     "&fields[items][offer][flags]=1"
#     "&fields[items][offer][bundles]=1"
#     "&fields[items][offer][gifts]=1"
#     "&fields[items][characteristics]=listing"
#     "&fields[quick_filters]=1"
#     "&search_id="
#     "&search_fraze="
#     "&search_key="
#     "&url=/televizoare/p2/c"
# )

# # Пользовательские заголовки
# headers = {
#     "accept": "application/json",
#     "accept-language": "ru,en;q=0.9,uk;q=0.8",
#     "content-type": "application/json",  # Устанавливаем Content-Type для JSON
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
# }

# # Тело запроса для ScraperAPI
# payload = {
#     "apiKey": "7757eea384bafff7726179e7855bb664",  # Ваш API-ключ
#     "url": target_url,  # Целевой URL
#     "keep_headers": True,  # Указываем, что используем свои заголовки
#     "method": "GET",  # HTTP-метод
# }

# import json
# import time

# # # Проверка результата
# # if response.status_code == 200:
# #     print("Успешный запрос!")
# #     print(response.text)  # Ответ в виде текста (HTML или JSON)
# # else:
# #     print(f"Ошибка: {response.status_code}")
# #     print(response.text)
import requests

max_retries = 100  # Максимальное количество проверок статуса
retry_delay = 10  # Задержка между проверками (в секундах)
response = requests.get(
    "https://async.scraperapi.com/jobs/a0907e2d-6911-4357-b0be-39d0ea9edbad"
)
for _ in range(max_retries):
    json_response = response.json()
    job_status = json_response.get("status")

    if job_status == "finished":
        name_file = json_response.get("id")
        json_file = f"{name_file}.json"
        extracted_body = json_response.get("response", {}).get("body")

        if extracted_body:
            try:
                # Попытка обработать содержимое "body" как JSON
                cleaned_body = json.loads(extracted_body)

                # Сохранение результата в файл
                with open(json_file, "w", encoding="utf-8") as output_file:
                    json.dump(
                        cleaned_body,
                        output_file,
                        indent=4,
                        ensure_ascii=False,
                    )
                print(f"Результат сохранён в файл: {json_file}")
                break
            except json.JSONDecodeError as e:
                print(f"Ошибка при декодировании JSON из 'body': {e}")
                break
    else:
        print("Задача ещё не завершена, ожидаем...")
        time.sleep(retry_delay)

        # Повторный запрос для проверки статуса
        status_url = json_response.get("statusUrl")
        if status_url:
            response = requests.get(status_url)
        else:
            print("Не удалось получить URL для проверки статуса.")
            break
else:
    print("Задача не завершена в отведённое время.")
