import json
import os
import time

import pandas as pd


def convert_excel_to_json_edrpo(excel_path, json_path, batch_size=50000):
    """Конвертирует Excel файл в JSON файл, сохраняя все значения как строки"""
    start_time = time.time()
    print(f"Начало конвертации Excel в JSON... {excel_path}")

    # Получаем размер файла
    file_size_mb = os.path.getsize(excel_path) / (1024 * 1024)
    print(f"Размер Excel файла: {file_size_mb:.2f} MB")

    # Чтение Excel файла
    excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
    sheet_name = excel_file.sheet_names[0]  # Используем первый лист

    # Чтение заголовков
    header_df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=1)
    original_columns = header_df.columns.tolist()

    # Новые имена колонок
    new_columns = [
        "edrpou",
        "full_name",
        "short_name",
        "org_form",
        "address",
        "status",
        "status_date",
        "authorized_persons",
        "activity_types",
        "phones",
        "email",
        "registration_date",
    ]

    # Создаем или очищаем JSON файл
    with open(json_path, "w", encoding="utf-8") as f:
        f.write("[\n")  # Начало JSON массива

    # Флаг для отслеживания первой записи
    is_first_record = True
    skip_rows = 1  # Пропускаем заголовок
    total_rows = 0

    while True:
        # Чтение порции данных, все колонки как строки
        df_chunk = pd.read_excel(
            excel_file,
            sheet_name=sheet_name,
            skiprows=skip_rows,
            nrows=batch_size,
            header=None,
            names=original_columns,
            dtype=str,  # Все данные читаем как строки
        )

        # Если порция пуста, значит достигнут конец файла
        if df_chunk.empty:
            break

        # Переименование колонок
        df_chunk.columns = original_columns
        df_chunk = df_chunk.rename(columns=dict(zip(original_columns, new_columns)))

        # Конвертация DataFrame в JSON строки
        chunk_size = len(df_chunk)
        total_rows += chunk_size

        # Преобразуем пустые строки и None в null для JSON
        df_chunk = df_chunk.replace("", None)
        df_chunk = df_chunk.replace("nan", None)

        # Записываем каждую строку как JSON объект
        with open(json_path, "a", encoding="utf-8") as f:
            for _, row in df_chunk.iterrows():
                row_dict = row.to_dict()

                # Добавляем запятую перед записью, кроме первой записи
                if not is_first_record:
                    f.write(",\n")
                else:
                    is_first_record = False

                # Записываем JSON объект
                json.dump(row_dict, f, ensure_ascii=False)

        # Увеличиваем счетчик пропущенных строк
        skip_rows += chunk_size

        print(f"Обработано {total_rows} строк")

    # Закрываем JSON массив
    with open(json_path, "a", encoding="utf-8") as f:
        f.write("\n]")

    end_time = time.time()
    duration = end_time - start_time
    json_size_mb = os.path.getsize(json_path) / (1024 * 1024)

    print(f"Конвертация завершена за {duration:.2f} секунд")
    print(f"Всего записей: {total_rows}")
    print(f"Размер JSON файла: {json_size_mb:.2f} MB")

    return total_rows


def convert_excel_to_json_finance(excel_path, json_path, year=2024, batch_size=50000):
    """Конвертирует Excel с финансовыми данными в JSON файл, очищая и нормализуя значения"""
    start_time = time.time()
    print(f"Начало конвертации Excel с финансовыми данными в JSON... {excel_path}")

    # Получаем размер файла
    file_size_mb = os.path.getsize(excel_path) / (1024 * 1024)
    print(f"Размер Excel файла: {file_size_mb:.2f} MB")

    # Чтение Excel файла
    excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
    sheet_name = excel_file.sheet_names[0]  # Используем первый лист

    # Чтение заголовков
    header_df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=1)
    original_columns = header_df.columns.tolist()

    # Новые имена колонок (финансовые данные)
    new_columns = [
        "edrpou",
        "number_of_employees",
        "katottg",
        "beginning_of_the_year_1012",
        "end_of_the_year_1012",
        "beginning_of_the_year_1195",
        "end_of_the_year_1195",
        "beginning_of_the_year_1495",
        "end_of_the_year_1495",
        "beginning_of_the_year_1595",
        "end_of_the_year_1595",
        "beginning_of_the_year_1695",
        "end_of_the_year_1695",
        "beginning_of_the_year_1900",
        "end_of_the_year_1900",
        "beginning_of_the_year_2000",
        "end_of_the_year_2000",
        "beginning_of_the_year_2280",
        "end_of_the_year_2280",
        "beginning_of_the_year_2285",
        "end_of_the_year_2285",
        "beginning_of_the_year_2350",
        "end_of_the_year_2350",
        "beginning_of_the_year_1621",
        "end_of_the_year_1621",
        "beginning_of_the_year_2465",
        "end_of_the_year_2465",
        "beginning_of_the_year_2505",
        "end_of_the_year_2505",
        "beginning_of_the_year_2510",
        "end_of_the_year_2510",
        "beginning_of_the_year_2355",
        "end_of_the_year_2355",
    ]

    # Создаем проверку соответствия колонок
    if len(original_columns) != len(new_columns):
        print(
            f"Предупреждение: количество колонок в Excel ({len(original_columns)}) не соответствует ожидаемому ({len(new_columns)})"
        )
        print(f"Оригинальные заголовки: {original_columns}")
        print(f"Ожидаемые заголовки: {new_columns}")

        # Если количество колонок не совпадает, используем только доступные колонки
        new_columns = new_columns[: len(original_columns)]

    # Создаем или очищаем JSON файл
    with open(json_path, "w", encoding="utf-8") as f:
        f.write("[\n")  # Начало JSON массива

    # Флаг для отслеживания первой записи
    is_first_record = True
    skip_rows = 1  # Пропускаем заголовок
    total_rows = 0

    # Функция для очистки числовых значений от суффиксов и пробелов
    def clean_numeric_value(value):
        if value is None or pd.isna(value) or value == "" or value == "NaN":
            return None

        if isinstance(value, str):
            # Убираем "тис. грн" и другие суффиксы
            value = value.replace("тис. грн", "").replace("тис.грн", "").strip()
            # Заменяем запятую на точку (если используется как десятичный разделитель)
            value = value.replace(",", ".")
            # Убираем пробелы между цифрами
            value = "".join(value.split())

            if value == "":
                return None
        return value

    # Функция для очистки EDRPOU от лишних символов
    def clean_edrpou(value):
        if value is None or pd.isna(value) or value == "" or value == "NaN":
            return None

        if isinstance(value, str):
            # Удаляем все непечатаемые символы и пробелы
            value = "".join(c for c in value if c.isdigit())

            if value == "":
                return None
        return value

    while True:
        # Чтение порции данных, все колонки как строки
        df_chunk = pd.read_excel(
            excel_file,
            sheet_name=sheet_name,
            skiprows=skip_rows,
            nrows=batch_size,
            header=None,
            names=original_columns,
            dtype=str,  # Все данные читаем как строки
        )

        # Если порция пуста, значит достигнут конец файла
        if df_chunk.empty:
            break

        # Переименование колонок
        df_chunk.columns = original_columns
        rename_dict = {
            original_columns[i]: new_columns[i]
            for i in range(min(len(original_columns), len(new_columns)))
        }
        df_chunk = df_chunk.rename(columns=rename_dict)

        # Конвертация DataFrame в JSON строки
        chunk_size = len(df_chunk)
        total_rows += chunk_size

        # Преобразуем пустые строки и None в null для JSON
        df_chunk = df_chunk.replace("", None)
        df_chunk = df_chunk.replace("nan", None)

        # Записываем каждую строку как JSON объект
        with open(json_path, "a", encoding="utf-8") as f:
            for _, row in df_chunk.iterrows():
                row_dict = row.to_dict()

                # Очистка EDRPOU
                if "edrpou" in row_dict:
                    row_dict["edrpou"] = clean_edrpou(row_dict["edrpou"])

                # Очистка финансовых показателей
                for field in row_dict:
                    if field.startswith("beginning_of_the_year_") or field.startswith(
                        "end_of_the_year_"
                    ):
                        row_dict[field] = clean_numeric_value(row_dict[field])

                # Добавляем год отчетности
                row_dict["year"] = str(year)

                # Добавляем запятую перед записью, кроме первой записи
                if not is_first_record:
                    f.write(",\n")
                else:
                    is_first_record = False

                # Записываем JSON объект
                json.dump(row_dict, f, ensure_ascii=False)

        # Увеличиваем счетчик пропущенных строк
        skip_rows += chunk_size

        print(f"Обработано {total_rows} строк")

    # Закрываем JSON массив
    with open(json_path, "a", encoding="utf-8") as f:
        f.write("\n]")

    end_time = time.time()
    duration = end_time - start_time
    json_size_mb = os.path.getsize(json_path) / (1024 * 1024)

    print(f"Конвертация завершена за {duration:.2f} секунд")
    print(f"Всего записей: {total_rows}")
    print(f"Размер JSON файла: {json_size_mb:.2f} MB")
    print(f"Год отчетности: {year}")

    return total_rows


# Пример использования
if __name__ == "__main__":
    # convert_excel_to_json_edrpo("edrpo_data.xlsx", "edrpo_data.json", batch_size=50000)
    convert_excel_to_json_finance(
        "financial_data.xlsx", "financial_data.json", year=2024
    )
