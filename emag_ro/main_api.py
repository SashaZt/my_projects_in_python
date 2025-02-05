import base64

import requests

# Учетные данные
username = "resteqsp@gmail.com "
password = "Q7Hd.ATGCc5$ym2"

# Кодируем учетные данные в base64
auth_string = f"{username}:{password}"
auth_encoded = base64.b64encode(auth_string.encode()).decode()

# Заголовки запроса
headers = {"Authorization": f"Basic {auth_encoded}", "Content-Type": "application/json"}

# URL API
api_url = "https://marketplace-api.emag.ro/api-3"

# Отправляем тестовый запрос
response = requests.get(f"{api_url}category/read", headers=headers, timeout=30)

# Вывод результата
print(response.status_code)
print(response.json())
