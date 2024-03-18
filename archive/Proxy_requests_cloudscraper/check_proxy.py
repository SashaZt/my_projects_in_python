import requests

proxies = {
    'http': 'http://b0jfDm:X5BYkt@94.127.138.110:8000',
    'https': 'http://b0jfDm:X5BYkt@94.127.138.110:8000',
}

try:
    response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=5)
    print(response.json())
except requests.exceptions.RequestException as err:
    print("Ошибка соединения:", err)
except requests.exceptions.HTTPError as errh:
    print("Ошибка Http:", errh)
except requests.exceptions.ConnectionError as errc:
    print("Ошибка подключения:", errc)
except requests.exceptions.Timeout as errt:
    print("Timeout Error:", errt)
