import csv
from itertools import combinations










def extract_data_from_csv():
    csv_filename = 'Test1.csv'
    columns_to_extract = ['title']

    data = []  # Создаем пустой список для хранения данных

    with open(csv_filename, 'r', newline='', encoding='utf-16') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')  # Указываем разделитель точку с запятой

        for row in reader:
            item = {}  # Создаем пустой словарь для текущей строки
            for column in columns_to_extract:
                item[column] = row[column]  # Извлекаем значения только для указанных столбцов
            data.append(item)  # Добавляем словарь в список
    return data

def extract_data_black_csv():
    csv_filename = 'black_list.csv'

    data = []  # Создаем пустой список для хранения данных

    with open(csv_filename, 'r', newline='', encoding='utf-16') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')  # Указываем разделитель точку с запятой

        for row in reader:
            if row:  # Убедимся, что строка не пустая
                black_row = row[0]  # Получаем первый элемент (первую колонку)
                data.append(black_row)
    return data


def count_title_occurrences():
    datas = extract_data_from_csv()
    black_datas = extract_data_black_csv()


    with open(f'replays_title.csv', 'w', newline='', encoding='utf-16') as file:
        writer = csv.writer(file, delimiter='\t')
        while True:
            print('Введите title')

            title = input()  # Ваша исходная строка
            # title = 'AMORTYZATOR PRAWY PRZÓD'  # Ваша исходная строка

            search_terms = title.upper().split()  # Разделяем строку на отдельные слова
            for num_words in range(2, len(search_terms) + 1):
                for combo in combinations(search_terms, num_words):
                    search_combo = ' '.join(combo)

                    # Проверяем, есть ли данная комбинация в black_datas
                    if search_combo not in black_datas:
                        count = 0  # Счетчик повторений title

                        # Проходим по каждому словарю в списке datas
                        for data in datas:
                            data_title = data.get('title', '').upper()
                            found_all_terms = all(term.upper() in data_title for term in
                                                  search_combo.split())
                            if found_all_terms:
                                count += 1
                        values = [search_combo, count]
                        print(values)

                        writer.writerow(values)


if __name__ == "__main__":
    count_title_occurrences()
