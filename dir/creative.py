import calendar
import os


def create_folders(month_year: str, base_path: str = "."):
    """
    Создает папки для всех дней указанного месяца и года.

    :param month_year: Строка в формате MM-YYYY, например, "05-2024".
    :param base_path: Базовый путь, где создаются папки (по умолчанию текущая директория).
    """
    try:
        # Парсим месяц и год из строки
        month, year = map(int, month_year.split("-"))

        # Проверяем корректность месяца и года
        if month < 1 or month > 12:
            raise ValueError("Месяц должен быть от 1 до 12.")
        if year < 1:
            raise ValueError("Год должен быть положительным числом.")

        # Получаем количество дней в месяце
        num_days = calendar.monthrange(year, month)[1]

        # Формируем папки для каждого дня
        for day in range(1, num_days + 1):
            folder_name = f"{day:02d}.{month:02d}.{year}"
            folder_path = os.path.join(base_path, folder_name)

            # Создаем папку, если ее еще нет
            os.makedirs(folder_path, exist_ok=True)
            print(f"Создана папка: {folder_path}")

    except ValueError as e:
        print(f"Ошибка: {e}")
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")


# Пример использования
create_folders("12-2024")
