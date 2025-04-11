import json
import pandas as pd
from pathlib import Path
import os


def format_reference_numbers(ref_numbers):
    """Форматирует список референсных номеров в строку вида BRAND:NUM1!NUM2/BRAND2:NUM3"""
    if not ref_numbers:
        return ""

    formatted = []
    for manufacturer, numbers in ref_numbers.items():
        formatted.append(f"{manufacturer}:{'!'.join(numbers)}")
    return "/".join(formatted)


def format_applications(applications):
    """Форматирует список применений в строку вида BRAND:VEHICLE:TYPE:ENGINE"""
    if not applications:
        return ""

    formatted = []
    for app in applications:
        # Исключаем поле date, если оно есть
        app_data = {}
        for key, value in app.items():
            if key.lower() != "date":
                app_data[key] = value

        # Проверяем наличие всех необходимых полей
        required_fields = ["manufacturer", "vehicle", "type", "engine"]
        if all(field in app_data for field in required_fields):
            app_str = f"{app_data['manufacturer']}:{app_data['vehicle']}:{app_data['type']}:{app_data['engine']}"
            formatted.append(app_str)
        else:
            # Если не все поля присутствуют, объединяем имеющиеся
            values = [f"{key}:{value}" for key, value in app_data.items()]
            if values:
                formatted.append(":".join(values))

    return "/".join(formatted)


def process_json_folder_to_csv(json_dir, output_dir=None):
    """
    Обрабатывает все JSON файлы в указанной папке и создает CSV файл для каждой категории

    Args:
        json_dir (str): Путь к директории с JSON файлами
        output_dir (str, optional): Путь для сохранения CSV файлов. По умолчанию та же директория.
    """
    json_path = Path(json_dir)

    if not output_dir:
        output_dir = json_path.parent / "csv"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(exist_ok=True, parents=True)

    # Получаем список поддиректорий (категорий)
    categories = [d for d in json_path.iterdir() if d.is_dir()]

    for category_dir in categories:
        category_name = category_dir.name
        print(f"Обработка категории: {category_name}")

        # Получаем все JSON файлы в этой категории
        json_files = list(category_dir.glob("*.json"))

        if not json_files:
            print(f"В категории {category_name} не найдено JSON файлов")
            continue

        # Загружаем все JSON файлы
        all_data = []
        all_fields = set()

        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as file:
                    data = json.load(file)

                    # Обрабатываем специальные поля
                    if "reference_numbers" in data:
                        data["Номера аналогів"] = format_reference_numbers(
                            data["reference_numbers"]
                        )
                        del data["reference_numbers"]

                    if "applications" in data:
                        data["Застосованість авто"] = format_applications(
                            data["applications"]
                        )
                        del data["applications"]

                    # Используем downloaded_images вместо images для URL изображения
                    if "downloaded_images" in data and data["downloaded_images"]:
                        # Объединяем все пути к изображениям через запятую
                        data["image_url"] = ",".join(data["downloaded_images"])

                    # Удаляем оригинальное поле images, если оно есть
                    if "images" in data:
                        del data["images"]

                    # Удаляем поле downloaded_images, так как мы уже извлекли нужную информацию
                    if "downloaded_images" in data:
                        del data["downloaded_images"]

                    # Собираем все уникальные поля
                    all_fields.update(data.keys())

                    # Добавляем данные в общий список
                    all_data.append(data)
            except Exception as e:
                print(f"Ошибка при обработке файла {json_file}: {e}")

        if not all_data:
            print(
                f"Не удалось загрузить ни один JSON файл из категории {category_name}"
            )
            continue

        # Создаем DataFrame с учетом всех уникальных полей
        df = pd.DataFrame(all_data)

        # Определяем приоритетные поля, которые должны быть в начале таблицы (если они есть)
        priority_fields = [
            "product_name",
            "Номера аналогів",
            "Застосованість авто",
            "image_url",
        ]

        # Переупорядочиваем колонки: сначала приоритетные, потом остальные
        all_columns = []
        for field in priority_fields:
            if field in df.columns:
                all_columns.append(field)

        # Добавляем оставшиеся колонки
        remaining_columns = [col for col in df.columns if col not in all_columns]
        all_columns.extend(remaining_columns)

        # Применяем порядок колонок
        if all_columns:
            df = df[all_columns]

        # Заменяем все NaN на пробел во всех колонках
        df = df.fillna(" ")

        # Обрабатываем кодировку символов для windows-1251
        try:
            # Перед сохранением заменяем проблемные символы
            for column in df.columns:
                if df[column].dtype == "object":  # только для текстовых столбцов
                    df[column] = df[column].apply(
                        lambda x: (
                            x.encode("windows-1251", "replace").decode("windows-1251")
                            if isinstance(x, str)
                            else x
                        )
                    )

            # Сохраняем в CSV с кодировкой windows-1251
            output_file = output_dir / f"{category_name}.csv"
            df.to_csv(output_file, index=False, encoding="windows-1251", sep=";")

        except UnicodeEncodeError:
            # Если возникла ошибка кодировки, используем UTF-8
            print(
                f"Невозможно сохранить в windows-1251, используем UTF-8 для {category_name}"
            )
            output_file = output_dir / f"{category_name}.csv"
            df.to_csv(output_file, index=False, encoding="utf-8-sig", sep=";")

        print(f"Создан CSV файл для категории {category_name}: {output_file}")
        print(
            f"Обработано {len(all_data)} элементов, {len(all_columns)} уникальных полей"
        )


# Пример использования:
if __name__ == "__main__":
    json_directory = "json"  # Директория с JSON файлами
    output_directory = "csv"  # Директория для сохранения CSV файлов

    process_json_folder_to_csv(json_directory, output_directory)
