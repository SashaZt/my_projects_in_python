import random

file_path = "proxy.txt"


def load_proxies(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if '@' in line and ':' in line]
    except FileNotFoundError:
        print("File not found.")
        return []


def get_random_proxy(proxies):
    if proxies:
        return random.choice(proxies)
    else:
        print("Empty proxy list.")
        return None


def proba():
    proxies = load_proxies(file_path)
    proxy = get_random_proxy(proxies)
    if proxy:
        print(proxy)
    else:
        print("No proxy found.")


# Вызов функции proba для проверки
proba()