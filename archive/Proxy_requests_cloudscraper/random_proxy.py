import random
"""Указываем где хранится файл с прокси"""
file_path = "proxies.txt"
def load_proxies(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if '@' in line and ':' in line]


def get_random_proxy(proxies):
    return random.choice(proxies)

def main():
    """В любой функции вызываем этот код"""
    proxies = load_proxies(file_path)
    proxy = get_random_proxy(proxies)
    login_password, ip_port = proxy.split('@')
    login, password = login_password.split(':')
    ip, port = ip_port.split(':')
    proxy_dict = {
        "http": f"http://{login}:{password}@{ip}:{port}",
        "https": f"http://{login}:{password}@{ip}:{port}"
    }
    print(proxy_dict)
if __name__ == '__main__':
    main()