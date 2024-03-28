# Открываем файл для чтения
with open("proxy.txt", "r") as file:
    # Читаем строки из файла
    lines = file.readlines()

# Создаем пустой список для кортежей
proxies = []

# Цикл для обработки каждой строки из файла
for line in lines:
    # Убираем символ переноса строки (\n)
    line = line.strip()
    # Разделяем строку по символу ":"
    parts = line.split(":")
    # Создаем кортеж из полученных частей и добавляем его в список proxies
    proxies.append((parts[0], int(parts[1]), parts[2], parts[3]))

# Выводим список кортежей
print(proxies)
