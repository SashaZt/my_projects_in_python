# import base64

# import requests
# from requests.adapters import HTTPAdapter
# from requests.packages.urllib3.util.retry import Retry

# username = "resteqsp@gmail.com"
# password = "Q7Hd.ATGCc5$ym2"
# auth_string = f"{username}:{password}"
# base64_auth = base64.b64encode(auth_string.encode()).decode()


# # Заголовки запроса
# headers = {"Authorization": f"Basic {base64_auth}", "Content-Type": "application/json"}
# data = {"data": {}}

# # URL API
# api_url = "https://marketplace-api.emag.ro/api-3"

# # Отправляем тестовый запрос
# response = requests.get(f"{api_url}/category/read", headers=headers, timeout=30)

# # Вывод результата
# print(response.status_code)
# print(response.json())


import base64
import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

username = "resteqsp@gmail.com"
password = "Q7Hd.ATGCc5$ym2"
auth_string = f"{username}:{password}"
base64_auth = base64.b64encode(auth_string.encode()).decode()

headers = {"Authorization": f"Basic {base64_auth}", "Content-Type": "application/json"}

data = {"data": {"currentPage": 1, "itemsPerPage": 10}}

api_url = "https://marketplace-api.emag.ro/api-3"

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

response = session.post(
    f"{api_url}/category/read", headers=headers, json=data, timeout=30
)

# print(response.status_code)
# print(response.json())

with open("output_json_file.json", "w", encoding="utf-8") as json_file:
    json.dump(response.json(), json_file, ensure_ascii=False, indent=4)
