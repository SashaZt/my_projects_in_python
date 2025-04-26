import json

import requests

# Читаем сохраненный запрос
with open("login_request.json", "r", encoding="utf-8") as f:
    request_data = json.load(f)

# Получаем свежие cookies
session = requests.Session()
session.get("https://www.ziva-fitness.com/login/")
headers = request_data["headers"].copy()
headers["cookie"] = "; ".join(f"{k}={v}" for k, v in session.cookies.items())

# Обновляем логин и пароль (если нужно)
username = "hdsport2006@gmail.com"
password = "03CkAfC2"
payload = request_data["payload"]
payload["data"]["propertyValues"][0]["values"][0]["Value"] = username  # Логин
payload["data"]["propertyValues"][1]["values"][0]["Value"] = password  # Пароль
payload["data"]["propertyValues"][2]["values"][0]["Value"] = True  # PermanentLogin

# Отправляем POST-запрос
response = requests.post(url=request_data["url"], headers=headers, json=payload)

print("Статус ответа:", response.status_code)
print("Содержимое ответа:", response.text)
