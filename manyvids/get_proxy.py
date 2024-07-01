# Открываем файл для чтения
with open("proxies.txt", "r") as file:
    # Читаем строки из файла
    lines = file.readlines()

# Создаем пустой список для кортежей
proxies = []

# Цикл для обработки каждой строки из файла
for line in lines:
    # Убираем символ переноса строки (\n)
    line = line.strip()

    # Проверяем наличие протокола в начале строки
    if line.startswith("http://") or line.startswith("https://"):
        # Разделяем строку по символу "://"
        protocol_and_rest = line.split("://")
        protocol = protocol_and_rest[0]
        rest = protocol_and_rest[1]

        # Разделяем оставшуюся часть строки по символу "@" и ":"
        user_info, host_port = rest.split("@")
        user, password = user_info.split(":")
        host, port = host_port.split(":")

        # Создаем кортеж и добавляем его в список proxies
        proxies.append((protocol, user, password, host, int(port)))
    else:
        # Разделяем строку по символу ":"
        parts = line.split(":")
        # Создаем кортеж из полученных частей и добавляем его в список proxies
        proxies.append((parts[0], int(parts[1]), parts[2], parts[3]))

# Выводим список кортежей
print(proxies)
