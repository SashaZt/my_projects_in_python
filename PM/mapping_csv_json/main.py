import csv
import json
from copy import deepcopy
from typing import Any, Dict, List, Union

from config.logger import logger


class AdvancedCSVToJSONMapper:
    def __init__(self):
        """
        Продвинутый маппер CSV в JSON с поддержкой внешних конфигураций
        """
        self.json_template = {}
        self.field_mapping = {}

    def load_json_template(self, template_file_path: str) -> Dict[str, Any]:
        """
        Загрузка шаблона JSON из файла

        Args:
            template_file_path: Путь к файлу с шаблоном JSON

        Returns:
            Словарь с шаблоном JSON
        """
        try:
            with open(template_file_path, "r", encoding="utf-8") as file:
                self.json_template = json.load(file)
                logger.info(f"Шаблон JSON загружен из {template_file_path}")
                return self.json_template
        except FileNotFoundError:
            logger.error(f"Файл шаблона {template_file_path} не найден")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при разборе JSON шаблона: {e}")
            return {}
        except Exception as e:
            logger.error(f"Ошибка при загрузке шаблона: {e}")
            return {}

    def load_field_mapping(
        self, mapping_file_path: str
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Загрузка мапинга полей из JSON файла

        Args:
            mapping_file_path: Путь к файлу с мапингом полей

        Returns:
            Словарь с мапингом полей
        """
        try:
            with open(mapping_file_path, "r", encoding="utf-8") as file:
                self.field_mapping = json.load(file)
                logger.info(f"Мапинг полей загружен из {mapping_file_path}")
                return self.field_mapping
        except FileNotFoundError:
            logger.error(f"Файл мапинга {mapping_file_path} не найден")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при разборе JSON мапинга: {e}")
            return {}
        except Exception as e:
            logger.error(f"Ошибка при загрузке мапинга: {e}")
            return {}

    def read_csv(
        self, csv_file_path: str, encoding="utf-8", delimiter=","
    ) -> List[Dict[str, Any]]:
        """
        Чтение данных из CSV файла

        Args:
            csv_file_path: Путь к CSV файлу
            encoding: Кодировка файла
            delimiter: Разделитель CSV

        Returns:
            Список словарей с данными из CSV
        """
        data = []
        try:
            with open(csv_file_path, "r", encoding=encoding) as file:
                # Автоматическое определение разделителя
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                try:
                    delimiter = sniffer.sniff(sample).delimiter
                except:
                    delimiter = delimiter  # используем переданный разделитель

                csv_reader = csv.DictReader(file, delimiter=delimiter)
                for row_num, row in enumerate(csv_reader, 1):
                    # Удаляем пустые значения и пробелы
                    cleaned_row = {}
                    for k, v in row.items():
                        if k:  # проверяем что ключ не пустой
                            key = k.strip()
                            value = v.strip() if v else ""
                            cleaned_row[key] = value
                    data.append(cleaned_row)

                logger.info(f"Загружено {len(data)} записей из {csv_file_path}")
        except FileNotFoundError:
            logger.error(f"CSV файл {csv_file_path} не найден")
        except Exception as e:
            logger.error(f"Ошибка при чтении CSV файла: {e}")

        return data

    def get_default_value(self, template_value: Any) -> Any:
        """
        Получение значения по умолчанию на основе типа из шаблона

        Args:
            template_value: Значение из шаблона JSON

        Returns:
            Значение по умолчанию соответствующего типа
        """
        if isinstance(template_value, bool):
            return False
        elif isinstance(template_value, int):
            return 0
        elif isinstance(template_value, float):
            return 0.0
        elif isinstance(template_value, str):
            return ""
        elif isinstance(template_value, list):
            return []
        elif isinstance(template_value, dict):
            return {}
        elif template_value is None:
            return None
        else:
            return ""

    def find_csv_value(self, csv_row: Dict[str, str], json_field: str) -> str:
        """
        Поиск значения в CSV строке по мапингу полей

        Args:
            csv_row: Строка данных из CSV
            json_field: Поле JSON для которого ищем значение

        Returns:
            Найденное значение или пустая строка
        """
        if json_field not in self.field_mapping:
            return ""

        mapping = self.field_mapping[json_field]

        # Если мапинг - это строка
        if isinstance(mapping, str):
            return csv_row.get(mapping, "")

        # Если мапинг - это список возможных полей
        elif isinstance(mapping, list):
            for csv_field in mapping:
                if csv_field in csv_row and csv_row[csv_field]:
                    return csv_row[csv_field]
            return ""

        return ""

    def convert_value_type(self, value: str, template_value: Any) -> Any:
        """
        Конвертация значения в нужный тип на основе шаблона

        Args:
            value: Строковое значение из CSV
            template_value: Значение из шаблона для определения типа

        Returns:
            Сконвертированное значение
        """
        if not value:
            return self.get_default_value(template_value)

        try:
            if isinstance(template_value, bool):
                return value.lower() in ["true", "1", "yes", "да", "истина"]
            elif isinstance(template_value, int):
                return int(float(value))  # через float для обработки "10.0"
            elif isinstance(template_value, float):
                return float(value)
            elif isinstance(template_value, str):
                return str(value)
            else:
                return value
        except (ValueError, TypeError):
            return self.get_default_value(template_value)

    def fill_json_object(
        self, json_obj: Dict[str, Any], csv_row: Dict[str, str], prefix: str = ""
    ) -> None:
        """
        Рекурсивное заполнение JSON объекта данными из CSV

        Args:
            json_obj: JSON объект для заполнения
            csv_row: Строка данных из CSV
            prefix: Префикс для вложенных полей
        """
        for key, template_value in json_obj.items():
            current_field = f"{prefix}.{key}" if prefix else key

            if isinstance(template_value, dict):
                # Рекурсивная обработка вложенных объектов
                self.fill_json_object(json_obj[key], csv_row, current_field)
            elif isinstance(template_value, list) and template_value:
                # Обработка массивов
                if isinstance(template_value[0], dict):
                    # Массив объектов - создаем один элемент на основе шаблона
                    csv_value = self.find_csv_value(csv_row, current_field)
                    if csv_value:
                        new_item = deepcopy(template_value[0])
                        self.fill_json_object(new_item, csv_row, current_field)
                        json_obj[key] = [new_item]
                    else:
                        json_obj[key] = []
                else:
                    # Массив простых значений
                    csv_value = self.find_csv_value(csv_row, current_field)
                    if csv_value:
                        # Разбиваем по запятой если это строка
                        values = [v.strip() for v in csv_value.split(",") if v.strip()]
                        json_obj[key] = values
                    else:
                        json_obj[key] = []
            else:
                # Простое поле
                csv_value = self.find_csv_value(csv_row, current_field)
                json_obj[key] = self.convert_value_type(csv_value, template_value)

    def map_csv_to_json(self, csv_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Мапинг данных из CSV в JSON формат

        Args:
            csv_data: Данные из CSV файла

        Returns:
            Список JSON объектов
        """
        json_data = []

        for row_num, csv_row in enumerate(csv_data, 1):
            try:
                # Создаем глубокую копию шаблона
                json_obj = deepcopy(self.json_template)

                # Заполняем объект данными из CSV
                self.fill_json_object(json_obj, csv_row)

                json_data.append(json_obj)
            except Exception as e:
                logger.error(f"Ошибка при обработке строки {row_num}: {e}")
                continue

        logger.info(f"Обработано {len(json_data)} записей")
        return json_data

    def save_json(self, data: List[Dict[str, Any]], output_file: str, encoding="utf-8"):
        """
        Сохранение данных в JSON файл

        Args:
            data: Данные для сохранения
            output_file: Путь к выходному JSON файлу
            encoding: Кодировка файла
        """
        try:
            with open(output_file, "w", encoding=encoding) as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            logger.info(f"Данные успешно сохранены в {output_file}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла: {e}")

    def process_files(
        self, template_file: str, csv_file: str, mapping_file: str, output_file: str
    ):
        """
        Полный процесс обработки файлов

        Args:
            template_file: Путь к файлу шаблона JSON
            csv_file: Путь к CSV файлу
            mapping_file: Путь к файлу мапинга полей
            output_file: Путь к выходному JSON файлу
        """
        logger.info("=== Начало обработки ===")

        # Загружаем шаблон JSON
        if not self.load_json_template(template_file):
            logger.error("Не удалось загрузить шаблон JSON")
            return

        # Загружаем мапинг полей
        if not self.load_field_mapping(mapping_file):
            logger.error("Не удалось загрузить мапинг полей")
            return

        # Читаем CSV данные
        csv_data = self.read_csv(csv_file)
        if not csv_data:
            logger.error("Нет данных для обработки")
            return

        # Преобразуем данные
        json_data = self.map_csv_to_json(csv_data)

        # Сохраняем результат
        self.save_json(json_data, output_file)

        logger.info("=== Обработка завершена ===")


# Пример использования
if __name__ == "__main__":
    # Создаем маппер
    mapper = AdvancedCSVToJSONMapper()

    # # Создаем пример файла мапинга если его нет
    # if not os.path.exists("field_mapping.json"):
    #     create_sample_mapping_file()

    # Обрабатываем файлы
    mapper.process_files(
        template_file="template.json",  # Ваш шаблон JSON
        csv_file="data.csv",  # Ваш CSV файл
        mapping_file="field_mapping.json",  # Файл мапинга полей
        output_file="result.json",  # Результирующий JSON
    )
