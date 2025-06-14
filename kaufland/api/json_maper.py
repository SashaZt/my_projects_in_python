import json
import re
from typing import Any, Dict, List, Union


class JSONMapper:
    def __init__(self):
        # Конфигурация маппинга: целевое_поле -> источник_данных
        self.mapping_config = {
            "ean": "specifications.parametry.EAN (GTIN)",  # исправлено: parametry с маленькой буквы
            "attributes.title": "title",
            "attributes.manufacturer": "specifications.parametry.Marka",  # исправлено: parametry с маленькой буквы
            "attributes.category": "category_path.-1.name",  # последняя категория
            "attributes.description": "description.sections",  # изменено: обрабатываем все секции
            "attributes.picture": "images.all.original",  # изменено: забираем все изображения
        }

    def get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Получить значение по вложенному пути"""
        keys = path.split(".")
        current = data

        for key in keys:
            if current is None:
                return None

            # Обработка индексов массивов
            if key.lstrip("-").isdigit():
                index = int(key)
                if isinstance(current, list):
                    # Правильная обработка отрицательных индексов (как в Python)
                    actual_index = index if index >= 0 else len(current) + index
                    if 0 <= actual_index < len(current):
                        current = current[actual_index]
                    else:
                        return None
                else:
                    return None
            else:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None

        return current

    def set_nested_value_as_list(
        self, data: Dict[str, Any], path: str, value: List[Any]
    ) -> None:
        """Установить список значений по вложенному пути (для изображений)"""
        keys = path.split(".")
        current = data

        # Проходим по всем ключам кроме последнего
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Устанавливаем список как есть
        last_key = keys[-1]
        current[last_key] = value

    def set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Установить значение по вложенному пути"""
        keys = path.split(".")
        current = data

        # Проходим по всем ключам кроме последнего
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Устанавливаем значение для последнего ключа
        last_key = keys[-1]
        if value is not None and value != "":
            # Все значения оборачиваем в массив согласно целевой структуре
            current[last_key] = [value] if not isinstance(value, list) else value

    def extract_all_images(self, images: List[Dict[str, Any]]) -> List[str]:
        """Извлечь все URL изображений"""
        image_urls = []
        for image in images:
            original_url = image.get("original", "")
            if original_url:
                image_urls.append(original_url)
        return image_urls  # ИСПРАВЛЕНО: добавлен return

    def extract_ean_from_images(self, images: List[Dict[str, Any]]) -> str:
        """Извлечь EAN из alt-текста изображений"""
        for image in images:
            alt_text = image.get("alt", "")
            if "EAN" in alt_text:
                # Ищем паттерн EAN (GTIN) XXXXXXXXX
                ean_match = re.search(r"EAN \(GTIN\) (\d+)", alt_text)
                if ean_match:
                    return ean_match.group(1)
        return ""

    def extract_description(self, description_data: Dict[str, Any]) -> str:
        """Извлечь описание из сложной структуры"""
        if not description_data or "sections" not in description_data:
            return ""

        description_parts = []
        for section in description_data["sections"]:
            if "items" in section:
                for item in section["items"]:
                    # Обрабатываем только текстовые элементы (TEXT или text)
                    if item.get("type", "").upper() == "TEXT" and item.get("content"):
                        description_parts.append(item["content"])

        return " ".join(description_parts)

    def map_item(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Маппинг данных товара"""
        result = {}

        for target_path, source_path in self.mapping_config.items():
            value = None

            # Специальная обработка для EAN
            if target_path == "ean":
                # Сначала пробуем получить из specifications
                value = self.get_nested_value(source_data, source_path)
                # Если не найден, пробуем извлечь из изображений
                if not value and "images" in source_data:
                    value = self.extract_ean_from_images(source_data["images"])
            # Специальная обработка для изображений
            elif source_path == "images.all.original":
                if "images" in source_data:
                    value = self.extract_all_images(source_data["images"])
            # Специальная обработка для описания
            elif source_path == "description.sections":
                value = self.extract_description(source_data.get("description", {}))
            else:
                value = self.get_nested_value(source_data, source_path)

            # ИСПРАВЛЕНО: Код установки значения перенесен ВНУТРЬ цикла
            # Устанавливаем значение если оно есть
            if value is not None and value != "":
                # Для изображений value уже является списком, не нужно оборачивать
                if target_path == "attributes.picture" and isinstance(value, list):
                    self.set_nested_value_as_list(result, target_path, value)
                else:
                    self.set_nested_value(result, target_path, value)

        return result

    def add_mapping(self, target_path: str, source_path: str) -> None:
        """Добавить новое правило маппинга"""
        self.mapping_config[target_path] = source_path

    def remove_mapping(self, target_path: str) -> None:
        """Удалить правило маппинга"""
        if target_path in self.mapping_config:
            del self.mapping_config[target_path]

    def get_mapping_config(self) -> Dict[str, str]:
        """Получить текущую конфигурацию маппинга"""
        return self.mapping_config.copy()


def load_product_data(file_path: str = "17241140591.json"):
    """Загрузка данных из JSON файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка при загрузке данных из {file_path}: {e}")
        return None


# Пример использования
def main():
    # Создаем маппер
    mapper = JSONMapper()

    # Загружаем данные
    source_item = load_product_data()

    if source_item is None:
        print("Не удалось загрузить данные")
        return

    # Выполняем маппинг
    mapped_item = mapper.map_item(source_item)

    # Выводим результат
    print("Результат маппинга:")
    print(json.dumps(mapped_item, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
