import os
import csv
def main():
    # Открываем CSV-файл с помощью модуля csv
    with open('url.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        # Проходим по каждой строке CSV-файла
        for row in reader:
            url = row[0]
            # Извлекаем номер из URL-адреса
            num = url.split('/')[-2]
            # Проверяем наличие файлов для каждой языковой версии
            for lang in ['ru', 'ua']:
                filename = f"c:\\grandinstrument\\data_{lang}\\{num}.html"
                if os.path.exists(filename):
                    continue
                else:
                    print(f"{filename} не найден в папке data_{lang}")


if __name__ == '__main__':
    main()
