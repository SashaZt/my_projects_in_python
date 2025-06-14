import csv
import json
import re
from copy import deepcopy
from io import StringIO
from typing import Any, Dict, List, Set, Union

from config.logger import logger


class AdvancedCSVToJSONMapper:
    def __init__(self, protected_fields: List[str] = None):
        """
        Продвинутый маппер CSV в JSON с поддержкой внешних конфигураций

        Args:
            protected_fields: Список полей которые не должны изменяться при мапинге
        """
        self.json_template = {}
        self.field_mapping = {}
        self.protected_fields = set(protected_fields or [])

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
                # logger.info(f"Шаблон JSON загружен из {template_file_path}")
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

    def load_protected_fields(self, protected_fields_file: str = None) -> Set[str]:
        """
        Загрузка списка защищенных полей из файла

        Args:
            protected_fields_file: Путь к JSON файлу со списком защищенных полей

        Returns:
            Множество защищенных полей
        """
        if not protected_fields_file:
            return self.protected_fields

        try:
            with open(protected_fields_file, "r", encoding="utf-8") as file:
                protected_data = json.load(file)

                # Поддерживаем разные форматы файла
                if isinstance(protected_data, list):
                    # Простой список: ["success", "active"]
                    self.protected_fields.update(protected_data)
                elif isinstance(protected_data, dict):
                    # Объект с описаниями: {"success": "Статус успеха", "active": "Активность"}
                    self.protected_fields.update(protected_data.keys())

                # logger.info(
                #     f"Загружено {len(protected_data)} защищенных полей из {protected_fields_file}"
                # )
                # logger.info(f"Защищенные поля: {list(self.protected_fields)}")
                return self.protected_fields

        except FileNotFoundError:
            logger.warning(
                f"Файл защищенных полей {protected_fields_file} не найден, используем настройки по умолчанию"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при разборе файла защищенных полей: {e}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке защищенных полей: {e}")

        return self.protected_fields

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
                # logger.info(f"Мапинг полей загружен из {mapping_file_path}")
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

    def add_protected_fields(self, *fields: str):
        """
        Добавление полей в список защищенных

        Args:
            *fields: Поля для защиты
        """
        self.protected_fields.update(fields)
        logger.info(f"Добавлены защищенные поля: {list(fields)}")
        logger.info(f"Всего защищенных полей: {list(self.protected_fields)}")

    def remove_protected_fields(self, *fields: str):
        """
        Удаление полей из списка защищенных

        Args:
            *fields: Поля для удаления из защиты
        """
        for field in fields:
            self.protected_fields.discard(field)
        logger.info(f"Удалены из защищенных полей: {list(fields)}")
        logger.info(f"Остались защищенными: {list(self.protected_fields)}")

    def is_protected_field(self, field_path: str) -> bool:
        """
        Проверка является ли поле защищенным

        Args:
            field_path: Путь к полю (например: "success" или "specifications.Parametry.Marka")

        Returns:
            True если поле защищено
        """
        # Проверяем точное соответствие
        if field_path in self.protected_fields:
            return True

        # Проверяем соответствие по частям пути для вложенных полей
        field_parts = field_path.split(".")
        for i in range(len(field_parts)):
            partial_path = ".".join(field_parts[: i + 1])
            if partial_path in self.protected_fields:
                return True

        return False

    def detect_delimiter_smart(self, file_content: str, sample_size: int = 2048) -> str:
        """
        Умное определение разделителя CSV файла

        Args:
            file_content: Содержимое файла
            sample_size: Размер выборки для анализа

        Returns:
            Определенный разделитель
        """
        sample = file_content[:sample_size]

        # Метод 1: Стандартный csv.Sniffer
        sniffer = csv.Sniffer()
        try:
            # Расширенный список разделителей для проверки
            delimiter = sniffer.sniff(sample, delimiters=",;\t|:").delimiter
            logger.debug(f"Sniffer определил разделитель: {repr(delimiter)}")
            return delimiter
        except Exception as e:
            logger.debug(f"Sniffer не смог определить разделитель: {e}")

        # Метод 2: Анализ частотности и консистентности
        possible_delimiters = [",", ";", "\t", "|", ":", " "]
        best_delimiter = ","
        best_score = 0

        lines = [line.strip() for line in sample.split("\n")[:10] if line.strip()]

        if not lines:
            return ","

        for delimiter in possible_delimiters:
            try:
                field_counts = []
                valid_lines = 0

                for line in lines:
                    if line:
                        # Разбиваем строку по разделителю
                        fields = line.split(delimiter)

                        # Проверяем что поля разумного размера
                        valid_fields = [
                            f.strip()
                            for f in fields
                            if f.strip() and len(f.strip()) <= 200
                        ]

                        # Минимум 2 поля для валидного CSV
                        if len(valid_fields) >= 2:
                            field_counts.append(len(valid_fields))
                            valid_lines += 1

                if not field_counts or valid_lines < 2:
                    continue

                # Оценка консистентности (одинаковое количество полей)
                unique_counts = set(field_counts)
                consistency = (
                    1.0
                    if len(unique_counts) == 1
                    else 0.7 if len(unique_counts) <= 2 else 0.3
                )

                # Средние количество полей
                avg_fields = sum(field_counts) / len(field_counts)

                # Процент валидных строк
                validity = valid_lines / len(lines)

                # Общий скор
                score = avg_fields * consistency * validity

                logger.debug(
                    f"Разделитель {repr(delimiter)}: поля={avg_fields:.1f}, "
                    f"консистентность={consistency:.1f}, валидность={validity:.1f}, "
                    f"скор={score:.2f}"
                )

                if score > best_score:
                    best_score = score
                    best_delimiter = delimiter

            except Exception as e:
                logger.debug(f"Ошибка при анализе разделителя {repr(delimiter)}: {e}")
                continue

        logger.info(
            f"Определен разделитель: {repr(best_delimiter)} (скор: {best_score:.2f})"
        )
        return best_delimiter

    def validate_csv_structure(
        self, file_content: str, delimiter: str, max_lines: int = 5
    ) -> bool:
        """
        Проверка корректности структуры CSV с данным разделителем

        Args:
            file_content: Содержимое файла
            delimiter: Разделитель для проверки
            max_lines: Количество строк для проверки

        Returns:
            True если структура корректная
        """
        try:
            file_like = StringIO(file_content)
            reader = csv.reader(file_like, delimiter=delimiter)

            field_counts = []
            for i, row in enumerate(reader):
                if i >= max_lines:
                    break
                if row and any(field.strip() for field in row):  # Не пустая строка
                    field_counts.append(len(row))

            # Проверяем что количество полей консистентно
            if field_counts:
                unique_counts = set(field_counts)
                return len(unique_counts) <= 2 and max(field_counts) >= 2

            return False

        except Exception:
            return False

    def read_csv(
        self, csv_file_path: str, encoding="utf-8", delimiter=","
    ) -> List[Dict[str, Any]]:
        """
        Чтение данных из CSV файла с улучшенным автоопределением разделителя

        Args:
            csv_file_path: Путь к CSV файлу
            encoding: Кодировка файла
            delimiter: Разделитель CSV (используется как fallback)

        Returns:
            Список словарей с данными из CSV
        """
        data = []
        original_delimiter = delimiter  # Сохраняем оригинальный разделитель

        try:
            # Пробуем разные кодировки для обработки BOM
            encodings_to_try = ["utf-8-sig", "utf-8", "cp1251", "latin1", "iso-8859-1"]

            # Если задана конкретная кодировка, пробуем её первой
            if encoding and encoding not in encodings_to_try:
                encodings_to_try.insert(0, encoding)
            elif encoding in encodings_to_try:
                # Перемещаем заданную кодировку в начало списка
                encodings_to_try.remove(encoding)
                encodings_to_try.insert(0, encoding)

            file_content = None
            used_encoding = None

            for enc in encodings_to_try:
                try:
                    with open(csv_file_path, "r", encoding=enc) as file:
                        file_content = file.read()
                        used_encoding = enc
                        break
                except UnicodeDecodeError:
                    continue

            if file_content is None:
                raise Exception(
                    f"Не удалось прочитать файл ни с одной из кодировок: {encodings_to_try}"
                )

            logger.info(f"Файл CSV прочитан с кодировкой: {used_encoding}")

            # Автоматическое определение разделителя
            detected_delimiter = self.detect_delimiter_smart(file_content)

            # Проверяем качество автоопределения
            if self.validate_csv_structure(file_content, detected_delimiter):
                delimiter = detected_delimiter
                logger.info(
                    f"Используется автоопределенный разделитель: {repr(delimiter)}"
                )
            else:
                # Если автоопределение не сработало, пробуем исходный разделитель
                if self.validate_csv_structure(file_content, original_delimiter):
                    delimiter = original_delimiter
                    logger.info(f"Используется заданный разделитель: {repr(delimiter)}")
                else:
                    # В крайнем случае пробуем популярные разделители
                    fallback_delimiters = [",", ";", "\t", "|"]
                    delimiter_found = False

                    for fallback_del in fallback_delimiters:
                        if self.validate_csv_structure(file_content, fallback_del):
                            delimiter = fallback_del
                            logger.info(
                                f"Используется fallback разделитель: {repr(delimiter)}"
                            )
                            delimiter_found = True
                            break

                    if not delimiter_found:
                        delimiter = original_delimiter
                        logger.warning(
                            f"Не удалось определить разделитель, используется: {repr(delimiter)}"
                        )

            # Создаем StringIO для обработки содержимого
            file_like = StringIO(file_content)
            csv_reader = csv.DictReader(file_like, delimiter=delimiter)

            for row_num, row in enumerate(csv_reader, 1):
                # Удаляем BOM и пустые значения
                cleaned_row = {}
                has_data = False

                for k, v in row.items():
                    if k:  # проверяем что ключ не пустой
                        # Удаляем BOM из ключа если есть
                        key = k.replace("\ufeff", "").strip()
                        # Удаляем BOM из значения если есть
                        value = v.replace("\ufeff", "").strip() if v else ""

                        if key:  # добавляем только если ключ не пустой после очистки
                            cleaned_row[key] = value
                            if value:  # Проверяем есть ли данные в строке
                                has_data = True

                # Добавляем строку только если в ней есть данные
                if cleaned_row and has_data:
                    data.append(cleaned_row)

            logger.info(f"Загружено {len(data)} записей из {csv_file_path}")

            # Логируем информацию о структуре
            if data:
                logger.info(f"Колонки: {list(data[0].keys())}")
                sample_data = {k: v for k, v in list(data[0].items())[:3]}
                logger.debug(f"Пример данных: {sample_data}")

        except FileNotFoundError:
            logger.error(f"CSV файл {csv_file_path} не найден")
        except Exception as e:
            logger.error(f"Ошибка при чтении CSV файла: {e}")
            # В случае критической ошибки можно попробовать простое чтение
            try:
                logger.info("Попытка простого чтения с заданным разделителем...")
                with open(csv_file_path, "r", encoding="utf-8-sig") as file:
                    csv_reader = csv.DictReader(file, delimiter=original_delimiter)
                    for row in csv_reader:
                        cleaned_row = {
                            k.replace("\ufeff", "").strip(): v.strip() if v else ""
                            for k, v in row.items()
                            if k and k.strip()
                        }
                        if any(cleaned_row.values()):
                            data.append(cleaned_row)
                logger.info(f"Простое чтение: загружено {len(data)} записей")
            except Exception as e2:
                logger.error(f"Простое чтение также не сработало: {e2}")

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
        # Игнорируем конфигурационные поля
        if json_field.endswith("._config"):
            return ""

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
        Конвертация значения с сохранением исходного типа числа из CSV

        Args:
            value: Строковое значение из CSV
            template_value: Значение из шаблона для определения целевого типа

        Returns:
            Сконвертированное значение с сохранением точности
        """
        if not value:
            return self.get_default_value(template_value)

        try:
            if isinstance(template_value, bool):
                return value.lower() in ["true", "1", "yes", "да", "истина"]
            elif isinstance(template_value, (int, float)):
                # СТАРЫЙ КОД:
                # float_value = float(value)

                # НОВЫЙ КОД:
                normalized_value = self.normalize_number_string(value)
                # logger.debug(
                #     f"Конвертация поля {field_path}: '{value}' -> '{normalized_value}'"
                # )

                try:
                    float_value = float(normalized_value)

                    if float_value.is_integer():
                        return int(float_value)
                    else:
                        return float_value
                except ValueError as ve:
                    logger.warning(
                        f"Не удалось конвертировать '{normalized_value}' в число: {ve}"
                    )
                    return self.get_default_value(template_value)
            # elif isinstance(template_value, (int, float)):
            #     # НОВАЯ ЛОГИКА: Сохраняем исходное число из CSV
            #     # Сначала пробуем как число с плавающей точкой
            #     float_value = float(value)

            #     # Если это целое число (например 12.0), возвращаем int
            #     if float_value.is_integer():
            #         return int(float_value)
            #     else:
            #         # Иначе возвращаем float с исходной точностью
            #         return float_value
            elif isinstance(template_value, str):
                return str(value)
            else:
                return value
        except (ValueError, TypeError):
            return self.get_default_value(template_value)

    def normalize_number_string(self, value: str) -> str:
        """
        Нормализация числовой строки для разных локалей

        Обрабатывает:
        - 49,03 (польская локаль) -> 49.03
        - 1 234,56 -> 1234.56
        - 1,234.56 (американская) -> 1234.56
        - 1.234,56 (европейская) -> 1234.56
        """
        if not value or not isinstance(value, str):
            return value

        # Удаляем все пробелы
        cleaned = value.strip().replace(" ", "")

        # Если нет цифр - возвращаем как есть
        if not re.search(r"\d", cleaned):
            return value

        # Паттерн для польской локали: цифры,цифры (например 49,03)
        polish_pattern = r"^(\d+),(\d{1,2})$"

        # Проверяем польский формат (49,03)
        if re.match(polish_pattern, cleaned):
            result = cleaned.replace(",", ".")
            logger.debug(f"Польский формат: {value} -> {result}")
            return result

        # Если содержит только одну запятую в конце - считаем десятичной запятой
        if "," in cleaned and cleaned.count(",") == 1:
            comma_pos = cleaned.find(",")
            after_comma = cleaned[comma_pos + 1 :]

            # Если после запятой 1-2 цифры, считаем это десятичной запятой
            if len(after_comma) <= 2 and after_comma.isdigit():
                result = cleaned.replace(",", ".")
                logger.debug(f"Десятичная запятая: {value} -> {result}")
                return result

        # Возвращаем как есть, если не удалось распознать
        return cleaned

    def fill_json_object(
        self, json_obj: Dict[str, Any], csv_row: Dict[str, str], prefix: str = ""
    ) -> None:
        """
        Рекурсивное заполнение JSON объекта данными из CSV с учетом защищенных полей

        Args:
            json_obj: JSON объект для заполнения
            csv_row: Строка данных из CSV
            prefix: Префикс для вложенных полей
        """
        for key, template_value in json_obj.items():
            current_field = f"{prefix}.{key}" if prefix else key

            # ПРОВЕРЯЕМ ЗАЩИЩЕННОЕ ЛИ ПОЛЕ
            if self.is_protected_field(current_field):
                # logger.debug(f"Поле '{current_field}' защищено, пропускаем")
                continue  # Пропускаем защищенные поля

            if isinstance(template_value, dict):
                # Рекурсивная обработка вложенных объектов
                self.fill_json_object(json_obj[key], csv_row, current_field)
            elif isinstance(template_value, list):
                # ИСПРАВЛЕННАЯ ОБРАБОТКА МАССИВОВ
                if not template_value:
                    # Пустой массив - оставляем пустым
                    json_obj[key] = []
                elif isinstance(template_value[0], dict):
                    # Массив объектов
                    self._handle_array_of_objects(
                        json_obj, key, template_value[0], csv_row, current_field
                    )
                else:
                    # Массив простых значений
                    self._handle_array_of_values(json_obj, key, csv_row, current_field)
            else:
                # Простое поле
                csv_value = self.find_csv_value(csv_row, current_field)
                json_obj[key] = self.convert_value_type(csv_value, template_value)
        if not prefix:
            self.handle_description_structure(json_obj, csv_row)

    def _handle_array_of_objects(
        self,
        json_obj: Dict[str, Any],
        key: str,
        template_item: Dict[str, Any],
        csv_row: Dict[str, str],
        current_field: str,
    ) -> None:
        """
        Обработка массива объектов с поддержкой разбиения строки из CSV и объединения нескольких колонок
        """
        # Собираем данные из всех возможных колонок
        all_csv_values = self._collect_all_csv_values(csv_row, current_field)

        if all_csv_values:
            # НОВАЯ ЛОГИКА: Разбиваем строки и создаем массив объектов
            result_array = self._parse_multiple_csv_to_object_array(
                all_csv_values, template_item, current_field
            )
            json_obj[key] = result_array
        else:
            json_obj[key] = []

    def _get_array_parse_config(self, field_path: str) -> Dict[str, Any]:
        """
        Получение конфигурации разбора массива из мапинга
        """
        # Ищем конфигурацию в field_mapping
        config_key = f"{field_path}._config"

        if config_key in self.field_mapping:
            return self.field_mapping[config_key]

        # Настройки по умолчанию
        default_configs = {
            "images": {
                "delimiter": ["|", ";", ",", " | ", "||"],
                "target_field": "original",
            },
            "category_path": {
                "delimiter": [" > ", " >> ", " / ", "/", ">"],
                "target_field": "name",
            },
        }

        return default_configs.get(
            field_path, {"delimiter": ["|", ";", ","], "target_field": "original"}
        )

    def _parse_multiple_csv_to_object_array(
        self, csv_values: List[str], template_item: Dict[str, Any], field_path: str
    ) -> List[Dict[str, Any]]:
        """
        Парсинг нескольких строк из CSV в массив объектов
        """
        # Получаем настройки разбора из мапинга
        parse_config = self._get_array_parse_config(field_path)

        # Поддержка множественных разделителей
        delimiters = parse_config.get("delimiter", "|")
        if isinstance(delimiters, str):
            delimiters = [delimiters]

        # Поле в объекте куда записывать основное значение
        target_field = parse_config.get("target_field", "original")

        all_items = []

        # Обрабатываем каждую строку отдельно
        for csv_value in csv_values:
            if not csv_value:
                continue

            # Пробуем разделители по порядку и берем тот который дает больше частей
            best_split = [csv_value]  # По умолчанию - без разбиения
            best_delimiter = "нет"

            for delimiter in delimiters:
                split_result = [
                    v.strip() for v in csv_value.split(delimiter) if v.strip()
                ]
                # Если этот разделитель дает больше частей - используем его
                if len(split_result) > len(best_split):
                    best_split = split_result
                    best_delimiter = delimiter

            # logger.debug(
            #     f"Строка '{csv_value[:50]}...': разделитель '{best_delimiter}', частей: {len(best_split)}"
            # )

            # Создаем объекты для каждой части
            for value in best_split:
                new_obj = deepcopy(template_item)
                if target_field in new_obj:
                    new_obj[target_field] = value
                all_items.append(new_obj)

        # logger.info(
        #     f"Поле '{field_path}': создано {len(all_items)} объектов из {len(csv_values)} колонок"
        # )
        return all_items

    def _find_numbered_columns(
        self, csv_row: Dict[str, str], base_field: str
    ) -> List[str]:
        """
        Ищет пронумерованные колонки (Images1, Images2, Photos1, etc.)
        """
        numbered_values = []

        # Ищем колонки с номерами от 1 до 20
        for i in range(1, 21):
            numbered_field = f"{base_field}{i}"
            if numbered_field in csv_row and csv_row[numbered_field]:
                numbered_values.append(csv_row[numbered_field])

        # logger.debug(
        #     f"Найдено {len(numbered_values)} пронумерованных колонок для '{base_field}'"
        # )
        return numbered_values

    def _collect_all_csv_values(
        self, csv_row: Dict[str, str], json_field: str
    ) -> List[str]:
        """
        Собирает данные из всех возможных CSV колонок для одного JSON поля
        """
        if json_field not in self.field_mapping:
            return []

        mapping = self.field_mapping[json_field]
        all_values = []

        # Если мапинг - это строка
        if isinstance(mapping, str):
            value = csv_row.get(mapping, "")
            if value:
                all_values.append(value)

        # Если мапинг - это список возможных полей
        elif isinstance(mapping, list):
            for csv_field in mapping:
                # Ищем точное совпадение
                if csv_field in csv_row and csv_row[csv_field]:
                    all_values.append(csv_row[csv_field])

                # Ищем пронумерованные варианты (Images1, Images2, etc.)
                numbered_values = self._find_numbered_columns(csv_row, csv_field)
                all_values.extend(numbered_values)

        # logger.debug(
        #     f"Поле '{json_field}': найдено {len(all_values)} значений из колонок"
        # )
        return all_values

    def _handle_array_of_values(
        self,
        json_obj: Dict[str, Any],
        key: str,
        csv_row: Dict[str, str],
        current_field: str,
    ) -> None:
        """
        Обработка массива простых значений
        """
        csv_value = self.find_csv_value(csv_row, current_field)
        if csv_value:
            # Разбиваем по запятой если это строка с несколькими значениями
            if "," in csv_value:
                values = [v.strip() for v in csv_value.split(",") if v.strip()]
                json_obj[key] = values
            else:
                json_obj[key] = [csv_value]
        else:
            json_obj[key] = []

    def map_csv_to_json(self, csv_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Мапинг данных из CSV в JSON формат
        ГАРАНТИРУЕТ создание JSON объекта для каждой строки CSV

        Args:
            csv_data: Данные из CSV файла

        Returns:
            Список JSON объектов (по одному на каждую строку CSV)
        """
        json_data = []
        successful_rows = 0
        failed_rows = 0

        logger.info(f"Начинаем обработку {len(csv_data)} строк CSV")

        for row_num, csv_row in enumerate(csv_data, 1):
            try:
                # Создаем глубокую копию шаблона для каждой строки
                json_obj = deepcopy(self.json_template)

                # Заполняем объект данными из текущей строки CSV
                self.fill_json_object(json_obj, csv_row)

                # Добавляем созданный объект в результат
                json_data.append(json_obj)
                successful_rows += 1

                # Логируем прогресс каждые 100 строк
                if row_num % 100 == 0:
                    logger.info(f"Обработано {row_num} строк из {len(csv_data)}")

            except Exception as e:
                logger.error(f"Ошибка при обработке строки {row_num}: {e}")
                logger.error(f"Данные строки: {csv_row}")
                failed_rows += 1

                # Создаем пустой объект на основе шаблона даже при ошибке
                try:
                    empty_obj = deepcopy(self.json_template)
                    self._fill_with_defaults(empty_obj)
                    json_data.append(empty_obj)
                    logger.warning(f"Создан пустой объект для строки {row_num}")
                except Exception as inner_e:
                    logger.error(
                        f"Не удалось создать даже пустой объект для строки {row_num}: {inner_e}"
                    )

        logger.info(
            f"Обработка завершена: {successful_rows} успешно, {failed_rows} с ошибками"
        )
        logger.info(
            f"Создано {len(json_data)} JSON объектов из {len(csv_data)} строк CSV"
        )

        # ПРОВЕРКА: количество JSON объектов должно соответствовать количеству строк CSV
        if len(json_data) != len(csv_data):
            logger.warning(
                f"ВНИМАНИЕ: Количество JSON объектов ({len(json_data)}) не соответствует количеству строк CSV ({len(csv_data)})"
            )

        return json_data

    def _fill_with_defaults(self, json_obj: Dict[str, Any]) -> None:
        """
        Заполнение JSON объекта значениями по умолчанию
        """
        for key, value in json_obj.items():
            if isinstance(value, dict):
                self._fill_with_defaults(value)
            elif isinstance(value, list):
                json_obj[key] = []
            else:
                json_obj[key] = self.get_default_value(value)

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
            logger.info(f"Сохранено {len(data)} JSON объектов")
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла: {e}")

    def save_individual_json_files(
        self,
        data: List[Dict[str, Any]],
        output_directory: str,
        file_prefix: str = "item",
        encoding="utf-8",
    ):
        """
        Сохранение каждого JSON объекта в отдельный файл

        Args:
            data: Данные для сохранения
            output_directory: Папка для сохранения файлов
            file_prefix: Префикс для имен файлов
            encoding: Кодировка файлов
        """
        import os

        try:
            # Создаем папку если не существует
            os.makedirs(output_directory, exist_ok=True)

            successful_saves = 0
            failed_saves = 0

            logger.info(
                f"Начинаем сохранение {len(data)} файлов в папку {output_directory}"
            )

            for index, json_obj in enumerate(data):
                try:
                    # Формируем имя файла
                    filename = f"{file_prefix}_{index + 1:06d}.json"  # item_000001.json
                    filepath = os.path.join(output_directory, filename)

                    # Сохраняем объект в отдельный файл
                    with open(filepath, "w", encoding=encoding) as file:
                        json.dump(json_obj, file, ensure_ascii=False, indent=4)

                    successful_saves += 1

                    # Логируем прогресс каждые 1000 файлов
                    if (index + 1) % 1000 == 0:
                        logger.info(f"Сохранено {index + 1} файлов из {len(data)}")

                except Exception as e:
                    logger.error(f"Ошибка при сохранении файла {filename}: {e}")
                    failed_saves += 1

            logger.info(
                f"Сохранение завершено: {successful_saves} успешно, {failed_saves} с ошибками"
            )
            logger.info(f"Файлы сохранены в папке: {output_directory}")

            return successful_saves

        except Exception as e:
            logger.error(f"Ошибка при создании папки или сохранении файлов: {e}")
            return 0

    def handle_description_structure(
        self, json_obj: Dict[str, Any], csv_row: Dict[str, str]
    ) -> None:
        """
        Специальная обработка структуры description с автоматическим созданием секций и элементов

        Обрабатывает поля вида:
        - description.sections.0.items.0.content
        - description.sections.1.items.0.content
        И автоматически устанавливает type: "TEXT" если есть content

        Если нет данных - сохраняет пустую структуру из шаблона

        Args:
            json_obj: JSON объект для заполнения
            csv_row: Строка данных из CSV
        """
        if "description" not in json_obj:
            return

        # Ищем все description поля в мапинге
        description_fields = {
            field: mapping
            for field, mapping in self.field_mapping.items()
            if field.startswith("description.sections.") and field.endswith(".content")
        }

        # Если в мапинге нет description полей, оставляем структуру как в шаблоне
        if not description_fields:
            logger.debug(
                "Нет description полей в мапинге, оставляем структуру из шаблона"
            )
            return

        # Инициализируем структуру description если нужно
        if "sections" not in json_obj["description"]:
            json_obj["description"]["sections"] = []

        logger.debug(
            f"Найдено {len(description_fields)} description полей для обработки"
        )

        # Флаг для отслеживания есть ли хоть какие-то данные
        has_any_data = False

        # Обрабатываем каждое поле
        for field_path, csv_mapping in description_fields.items():
            try:
                # Извлекаем индекс секции из пути (например, description.sections.0.items.0.content -> 0)
                path_parts = field_path.split(".")
                if len(path_parts) >= 4 and path_parts[2].isdigit():
                    section_index = int(path_parts[2])

                    # Находим значение в CSV
                    content_value = self.find_csv_value(csv_row, field_path)

                    if content_value and content_value.strip():
                        # Проверяем защищенность поля
                        if self.is_protected_field(field_path):
                            logger.debug(f"Поле '{field_path}' защищено, пропускаем")
                            continue

                        # Убеждаемся что у нас достаточно секций
                        while len(json_obj["description"]["sections"]) <= section_index:
                            json_obj["description"]["sections"].append({"items": []})

                        # Получаем нужную секцию
                        target_section = json_obj["description"]["sections"][
                            section_index
                        ]

                        # Инициализируем items если нужно
                        if "items" not in target_section:
                            target_section["items"] = []

                        # Убеждаемся что есть хотя бы один элемент
                        if len(target_section["items"]) == 0:
                            target_section["items"].append({"type": "", "content": ""})

                        # Записываем content и автоматически устанавливаем type
                        target_section["items"][0]["content"] = content_value.strip()
                        target_section["items"][0]["type"] = "TEXT"

                        has_any_data = True
                        logger.debug(
                            f"Установлено description.sections[{section_index}].items[0]: content='{content_value[:50]}...', type='TEXT'"
                        )
                    else:
                        logger.debug(f"Нет данных для поля '{field_path}'")

            except (ValueError, IndexError, KeyError) as e:
                logger.error(
                    f"Ошибка при обработке description поля '{field_path}': {e}"
                )
                continue

        # Если не найдено никаких данных, но в шаблоне была структура - сохраняем пустую структуру из шаблона
        if not has_any_data:
            # Проверяем есть ли в шаблоне базовая структура sections
            if (
                json_obj["description"].get("sections") is None
                or len(json_obj["description"]["sections"]) == 0
            ):
                logger.debug(
                    "Нет данных для description, создаем пустую структуру из шаблона"
                )
                json_obj["description"]["sections"] = [
                    {"items": [{"type": "", "content": ""}]}
                ]
            else:
                # Если структура уже есть, просто убеждаемся что у нее правильный формат
                for section in json_obj["description"]["sections"]:
                    if "items" not in section:
                        section["items"] = []
                    if len(section["items"]) == 0:
                        section["items"].append({"type": "", "content": ""})
                    # Убеждаемся что пустые поля действительно пустые
                    for item in section["items"]:
                        if "type" not in item or not item["type"]:
                            item["type"] = ""
                        if "content" not in item or not item["content"]:
                            item["content"] = ""

    def process_files(
        self,
        template_file: str,
        csv_file: str,
        mapping_file: str,
        output_file: str = None,
        output_directory: str = None,
        save_as_individual_files: bool = False,
        protected_fields_file: str = None,
    ):
        """
        Полный процесс обработки файлов

        Args:
            template_file: Путь к файлу шаблона JSON
            csv_file: Путь к CSV файлу
            mapping_file: Путь к файлу мапинга полей
            output_file: Путь к выходному JSON файлу (если save_as_individual_files=False)
            output_directory: Папка для сохранения отдельных файлов (если save_as_individual_files=True)
            save_as_individual_files: True - сохранять каждый объект в отдельный файл, False - все в один файл
            protected_fields_file: Путь к файлу с защищенными полями
        """
        logger.info("=== Начало обработки ===")

        # Загружаем защищенные поля если указан файл
        if protected_fields_file:
            self.load_protected_fields(protected_fields_file)

        # Загружаем шаблон JSON
        if not self.load_json_template(template_file):
            logger.error("Не удалось загрузить шаблон JSON")
            return False

        # Загружаем мапинг полей
        if not self.load_field_mapping(mapping_file):
            logger.error("Не удалось загрузить мапинг полей")
            return False

        # # Показываем информацию о защищенных полях
        # if self.protected_fields:
        #     logger.info(
        #         f"Защищенные поля (не изменяются): {list(self.protected_fields)}"
        #     )

        # Читаем CSV данные
        csv_data = self.read_csv(csv_file)
        if not csv_data:
            logger.error("Нет данных для обработки")
            return False

        # Показываем как работает мапинг на первой строке
        if csv_data:
            logger.info("=== ДЕМОНСТРАЦИЯ МАПИНГА ===")
            self.show_processing_flow(csv_data[0])
            logger.info("")

        # Преобразуем данные
        json_data = self.map_csv_to_json(csv_data)

        # Проверяем результат
        if len(json_data) == 0:
            logger.error("Не удалось создать ни одного JSON объекта")
            return False

        # Сохраняем результат
        if save_as_individual_files:
            if not output_directory:
                logger.error("Не указана папка для сохранения отдельных файлов")
                return False
            saved_count = self.save_individual_json_files(json_data, output_directory)
            success = saved_count > 0
        else:
            if not output_file:
                logger.error("Не указан файл для сохранения")
                return False
            self.save_json(json_data, output_file)
            success = True

        if success:
            logger.info("=== Обработка завершена успешно ===")
        else:
            logger.error("=== Обработка завершена с ошибками ===")

        return success

    def validate_mapping(self) -> bool:
        """
        Валидация мапинга полей
        """
        if not self.field_mapping:
            logger.error("Мапинг полей пуст")
            return False

        logger.info(f"Найдено {len(self.field_mapping)} правил мапинга:")
        for json_field, csv_fields in self.field_mapping.items():
            logger.info(f"  {json_field} <- {csv_fields}")

        return True

    def show_processing_flow(self, csv_sample: Dict[str, str]):
        """
        Показывает как происходит процесс мапинга для примера строки

        Args:
            csv_sample: Пример строки из CSV для демонстрации
        """
        logger.info("=== ДЕМОНСТРАЦИЯ ПРОЦЕССА МАПИНГА ===")
        logger.info(f"Пример CSV строки: {csv_sample}")
        logger.info("")

        logger.info("Шаг 1: Читаем CSV колонки:")
        for i, (csv_key, csv_value) in enumerate(csv_sample.items(), 1):
            logger.info(f"  {i}. '{csv_key}' = '{csv_value}'")

        logger.info("")
        logger.info("Шаг 2: Применяем мапинг (CSV колонка → JSON поле):")

        mapped_fields = []
        for json_field, csv_variants in self.field_mapping.items():
            found_value = self.find_csv_value(csv_sample, json_field)
            if found_value:
                if isinstance(csv_variants, str):
                    matched_csv_field = (
                        csv_variants if csv_variants in csv_sample else "НЕ НАЙДЕНО"
                    )
                else:
                    matched_csv_field = None
                    for variant in csv_variants:
                        if variant in csv_sample and csv_sample[variant]:
                            matched_csv_field = variant
                            break
                    if not matched_csv_field:
                        matched_csv_field = "НЕ НАЙДЕНО"

                logger.info(
                    f"  ✅ {json_field} <- '{matched_csv_field}' = '{found_value}'"
                )
                mapped_fields.append((json_field, found_value))
            else:
                logger.info(f"  ❌ {json_field} <- {csv_variants} = НЕТ ДАННЫХ")

        logger.info("")
        logger.info("Шаг 3: Создаем JSON объект:")

        # Создаем пример JSON объекта
        json_obj = deepcopy(self.json_template)
        self.fill_json_object(json_obj, csv_sample)

        logger.info("  Структура JSON:")
        sample_json_str = (
            json.dumps(json_obj, ensure_ascii=False, indent=2)[:500] + "..."
        )
        logger.info(f"  {sample_json_str}")

        logger.info("=== КОНЕЦ ДЕМОНСТРАЦИИ ===")
        return json_obj


# Пример использования
if __name__ == "__main__":
    # СПОСОБ 1: Создаем маппер с защищенными полями в коде
    mapper = AdvancedCSVToJSONMapper(protected_fields=["success", "active"])

    # Обрабатываем файлы с защищенными полями
    logger.info("=== Сохранение в отдельные файлы с защищенными полями ===")
    success = mapper.process_files(
        template_file="template.json",
        csv_file="data.csv",
        mapping_file="field_mapping.json",
        output_directory="json_files",
        save_as_individual_files=True,
        protected_fields_file="protected_fields.json",  # Файл с защищенными полями
    )

    if success:
        logger.info("Все файлы обработаны успешно!")
    else:
        logger.error("Произошла ошибка при обработке файлов")
