#!/usr/bin/env python3
"""
Универсальный генератор config.py на основе JSON конфигурации
Автоматически создает переменные окружения по структуре JSON

Использование:
    python fixed_config_generator.py
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


class UniversalConfigGenerator:
    """Универсальный генератор конфигурации"""

    def __init__(
        self,
        json_file: str = "config.json",
        output_file: str = "client/config/config.py",
    ):
        self.json_file = Path(json_file)
        self.output_file = Path(output_file)
        self.config_data = {}
        self.used_class_names = set()
        self.class_contexts = {}
        self.env_vars_mapping = {}  # Автоматический маппинг

    def load_json_config(self) -> None:
        """Загружает JSON конфигурацию"""
        if not self.json_file.exists():
            raise FileNotFoundError(f"Файл {self.json_file} не найден")

        with open(self.json_file, "r", encoding="utf-8") as f:
            self.config_data = json.load(f)

    def _build_env_mapping(self, data: Dict[str, Any], prefix: str = "") -> None:
        """Автоматически строит маппинг переменных окружения"""
        for key, value in data.items():
            current_prefix = f"{prefix}_{key.upper()}" if prefix else key.upper()

            if isinstance(value, dict):
                # Рекурсивно обрабатываем вложенные объекты
                self._build_env_mapping(value, current_prefix)
            else:
                # Сохраняем маппинг: путь -> env_var
                path_key = (
                    f"{prefix.lower().replace('_', '.')}.{key}" if prefix else key
                )
                self.env_vars_mapping[path_key] = current_prefix

    def _get_unique_class_name(
        self, base_name: str, context: str = "", full_path: str = ""
    ) -> str:
        """Генерирует уникальное имя класса с учетом контекста"""
        structure_key = full_path or f"{context}.{base_name}" if context else base_name

        if structure_key in self.class_contexts:
            return self.class_contexts[structure_key]

        # Генерируем базовое имя с учетом родительского контекста
        if context and base_name in [
            "replacements",
            "rules",
            "rates",
            "modifications",
            "log",
            "format",
        ]:
            # Для replacements добавляем контекст (ru/ua)
            class_name = self._to_camel_case(f"{base_name}_{context}") + "Config"
        elif context and base_name in ["log"] and "client" in context.lower():
            # Для log в client добавляем префикс
            class_name = self._to_camel_case(f"{context}_{base_name}") + "Config"
        else:
            class_name = self._to_camel_case(base_name) + "Config"

        # Проверяем уникальность
        original_name = class_name
        counter = 1
        while class_name in self.used_class_names:
            class_name = f"{original_name}{counter}"
            counter += 1

        self.used_class_names.add(class_name)
        self.class_contexts[structure_key] = class_name
        return class_name

    def _to_camel_case(self, snake_str: str) -> str:
        """Преобразует snake_case в CamelCase"""
        components = snake_str.replace("-", "_").split("_")
        return "".join(word.capitalize() for word in components if word)

    def _get_python_type(self, value: Any) -> str:
        """Определяет Python тип для значения"""
        if isinstance(value, dict):
            return "Dict[str, Any]"
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                return "List[Dict[str, Any]]"
            elif value and isinstance(value[0], str):
                return "List[str]"
            elif value and isinstance(value[0], (int, float)):
                return f"List[{type(value[0]).__name__}]"
            else:
                return "List[Any]"
        elif isinstance(value, str):
            return "str"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, bool):
            return "bool"
        else:
            return "Any"

    def _get_default_value(self, value: Any, field_type: str) -> str:
        """Получает значение по умолчанию для поля с правильным типом"""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, (int, float, bool)):
            return str(value).lower() if isinstance(value, bool) else str(value)
        elif isinstance(value, list):
            if field_type.startswith("List"):
                return "field(default_factory=list)"
            return "None"
        elif isinstance(value, dict):
            return "None"
        else:
            return "None"

    def _generate_dataclass(
        self, name: str, data: Dict[str, Any], context: str = "", full_path: str = ""
    ) -> Tuple[str, str, Set[str]]:
        """Генерирует dataclass для секции конфигурации"""
        imports = set()
        current_path = f"{full_path}.{name}" if full_path else name
        class_name = self._get_unique_class_name(name, context, current_path)

        # Проверяем, не создавали ли уже этот класс
        if (
            current_path in self.class_contexts
            and self.class_contexts[current_path] != class_name
        ):
            return "", self.class_contexts[current_path], imports

        # Начало класса
        code = f"@dataclass\n"
        code += f"class {class_name}:\n"
        code += f'    """Конфигурация для {name}"""\n'

        # Поля класса
        fields = []
        nested_classes = []
        needs_field_import = False

        for field_name, field_value in data.items():
            if isinstance(field_value, dict):
                # Вложенный объект
                nested_code, nested_class_name, nested_imports = (
                    self._generate_dataclass(
                        field_name, field_value, name, current_path
                    )
                )
                if nested_code:
                    nested_classes.append(nested_code)
                imports.update(nested_imports)
                fields.append(
                    f"    {field_name}: {nested_class_name} = field(default_factory={nested_class_name})"
                )
                needs_field_import = True
            else:
                # Обычное поле
                field_type = self._get_python_type(field_value)
                default_value = self._get_default_value(field_value, field_type)

                if "field(default_factory=" in default_value:
                    needs_field_import = True

                if field_type.startswith("List"):
                    imports.add("List")
                if field_type.startswith("Dict"):
                    imports.add("Dict")
                if "Any" in field_type:
                    imports.add("Any")

                fields.append(f"    {field_name}: {field_type} = {default_value}")

        if needs_field_import:
            imports.add("field")

        # Добавляем поля к классу
        if fields:
            code += "\n".join(fields) + "\n"
        else:
            code += "    pass\n"

        # Объединяем вложенные классы с основным
        if nested_classes:
            full_code = "\n\n".join(nested_classes) + "\n\n" + code
        else:
            full_code = code

        return full_code, class_name, imports

    def _get_env_var_for_path(self, path: str) -> str:
        """Получает переменную окружения для пути"""
        # Нормализуем путь
        normalized_path = path.lower().replace("_", ".")

        # Ищем точное совпадение
        if normalized_path in self.env_vars_mapping:
            return self.env_vars_mapping[normalized_path]

        # Ищем частичное совпадение (для вложенных полей)
        for mapped_path, env_var in self.env_vars_mapping.items():
            if normalized_path.endswith(mapped_path.split(".")[-1]):
                return env_var

        # Генерируем базовое имя как fallback
        return path.upper().replace(".", "_")

    def _generate_constructor_code(
        self,
        section_name: str,
        data: Dict[str, Any],
        class_name: str,
        indent: str = "            ",
        parent_path: str = "",
    ) -> str:
        """Генерирует код конструктора для секции"""
        code = f"{indent}{section_name}={class_name}(\n"
        current_path = f"{parent_path}.{section_name}" if parent_path else section_name

        for field_name, field_value in data.items():
            field_path = f"{current_path}.{field_name}"

            if isinstance(field_value, dict):
                # Вложенный объект
                nested_path = f"{current_path}.{field_name}"
                nested_class_name = self.class_contexts.get(nested_path)
                if not nested_class_name:
                    nested_class_name = self._get_unique_class_name(
                        field_name, section_name, nested_path
                    )

                nested_code = self._generate_constructor_code(
                    field_name,
                    field_value,
                    nested_class_name,
                    indent + "    ",
                    current_path,
                )
                code += nested_code
            else:
                # Обычное поле
                env_var = self._get_env_var_for_path(field_path)
                field_type = type(field_value).__name__

                if field_type == "list":
                    code += f'{indent}    {field_name}=cls._parse_json_env_var("{env_var}", {json.dumps(field_value)}),\n'
                elif field_type == "bool":
                    code += f'{indent}    {field_name}=cls._get_env_bool("{env_var}", {str(field_value).lower()}),\n'
                elif field_type in ("int", "float"):
                    code += f'{indent}    {field_name}={field_type}(os.getenv("{env_var}", "{field_value}")),\n'
                else:
                    code += f'{indent}    {field_name}=os.getenv("{env_var}", "{field_value}"),\n'

        code += f"{indent}),\n"
        return code

    def generate(self) -> None:
        """Генерирует универсальную конфигурацию"""
        print(f"🔍 Загрузка {self.json_file}...")
        self.load_json_config()

        print("🗺️  Построение маппинга переменных окружения...")
        self._build_env_mapping(self.config_data)

        print("📝 Генерация кода...")

        # Начало файла
        code = """# client/config/config.py
# Автоматически сгенерировано на основе JSON конфигурации
# Для регенерации используйте: python fixed_config_generator.py

import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()


"""

        # Генерируем dataclasses
        all_imports = set()
        dataclass_codes = []
        main_fields = []
        constructor_parts = []

        for section_name, section_data in self.config_data.items():
            if isinstance(section_data, dict):
                class_code, class_name, imports = self._generate_dataclass(
                    section_name, section_data
                )
                if class_code:
                    dataclass_codes.append(class_code)
                all_imports.update(imports)
                main_fields.append(
                    f"    {section_name}: {class_name} = field(default_factory={class_name})"
                )

                # Генерируем код конструктора
                constructor_code = self._generate_constructor_code(
                    section_name, section_data, class_name
                )
                constructor_parts.append(constructor_code)
            else:
                # Простое поле в корне
                field_type = self._get_python_type(section_data)
                default_value = self._get_default_value(section_data, field_type)
                main_fields.append(
                    f"    {section_name}: {field_type} = {default_value}"
                )

        # Добавляем dataclasses
        code += "\n\n".join(dataclass_codes)

        # Главный класс Config
        code += '''


@dataclass
class Config:
    """Главная конфигурация приложения"""
'''

        # Поля главного класса
        if main_fields:
            code += "\n" + "\n".join(main_fields) + "\n"

        # Методы загрузки
        code += '''
    @classmethod
    def load(cls) -> "Config":
        """Загружает конфигурацию из .env файла"""
        config_path = Path(".env")
        if config_path.exists():
            return cls.from_env()
        else:
            raise RuntimeError("Файл конфигурации .env не найден")
    
    @classmethod
    def from_json(cls, json_path: str = "config.json") -> "Config":
        """Загружает конфигурацию из JSON файла"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Создаем экземпляры классов рекурсивно
        return cls._create_from_dict(data)
    
    @classmethod
    def _create_from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Рекурсивно создает объекты из словаря"""
        # Простая реализация - расширьте при необходимости
        return cls(**data)

    @classmethod
    def _parse_json_env_var(cls, var_name: str, default_value: Any = None) -> Any:
        """Парсит JSON из переменной окружения"""
        value = os.getenv(var_name)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                print(f"Ошибка парсинга JSON в переменной {var_name}: {value}")
                return default_value
        return default_value

    @classmethod
    def _get_env_bool(cls, var_name: str, default: bool = False) -> bool:
        """Получает булево значение из env"""
        value = os.getenv(var_name, "").lower()
        return value in ("true", "yes", "1", "on") if value else default
'''

        # Метод from_env
        code += '''
    @classmethod
    def from_env(cls) -> "Config":
        """Загружает конфигурацию из переменных окружения"""
        return cls(
'''

        # Добавляем части конструктора
        code += "".join(constructor_parts)

        code += """        )


# Пример использования
if __name__ == "__main__":
    try:
        config = Config.load()
        print("✅ Конфигурация успешно загружена")
        
        # Проверяем структуру
        sections = [attr for attr in dir(config) if not attr.startswith('_')]
        print(f"📋 Секций конфигурации: {len(sections)}")
        
        # Пример доступа (адаптируйте под вашу структуру)
        if hasattr(config, 'project'):
            print(f"🏗️  Проект: {config.project.name}")
            print(f"🌍 Окружение: {config.project.environment}")
        
        if hasattr(config, 'client'):
            print(f"⚡ Макс. воркеров: {config.client.max_workers}")
        
        if hasattr(config, 'db'):
            print(f"🗄️  База данных: {config.db.name}@{config.db.host}:{config.db.port}")
        
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
"""

        # Создаем директорию и записываем файл
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(code)

        print(f"✅ Универсальная конфигурация сгенерирована: {self.output_file}")
        print(f"📈 Создано классов: {len(dataclass_codes)}")
        print(f"🗂️  Переменных окружения: {len(self.env_vars_mapping)}")

        # Генерируем .env файла
        # self._generate_env_file()

    # def _generate_env_file(self) -> None:
    #     """Генерирует .env файл на основе JSON"""
    #     env_file_path = self.output_file.parent / ".env.generated"

    #     env_content = "# Автоматически сгенерированный .env файл\n"
    #     env_content += "# Основан на структуре config.json\n\n"

    #     # Группируем по секциям
    #     sections = {}
    #     for path, env_var in self.env_vars_mapping.items():
    #         section = path.split(".")[0] if "." in path else "ROOT"
    #         if section not in sections:
    #             sections[section] = []

    #         # Находим значение в JSON
    #         value = self._get_value_by_path(path)
    #         sections[section].append((env_var, value))

    #     # Генерируем контент
    #     for section_name, vars_list in sections.items():
    #         env_content += f"\n# {section_name.upper()} Configuration\n"
    #         for env_var, value in vars_list:
    #             if isinstance(value, str):
    #                 env_content += f'{env_var}="{value}"\n'
    #             elif isinstance(value, (list, dict)):
    #                 env_content += f"{env_var}='{json.dumps(value)}'\n"
    #             else:
    #                 env_content += f"{env_var}={value}\n"

    #     with open(env_file_path, "w", encoding="utf-8") as f:
    #         f.write(env_content)

    #     print(f"📋 Создан .env файл: {env_file_path}")

    def _get_value_by_path(self, path: str) -> Any:
        """Получает значение из JSON по пути"""
        parts = path.split(".")
        value = self.config_data

        try:
            for part in parts:
                value = value[part]
            return value
        except (KeyError, TypeError):
            return ""

    def print_env_mapping(self) -> None:
        """Выводит маппинг переменных окружения"""
        print("\n🗺️  Маппинг переменных окружения:")
        for path, env_var in sorted(self.env_vars_mapping.items()):
            print(f"  {path} -> {env_var}")


def main():
    """Главная функция"""
    import argparse

    parser = argparse.ArgumentParser(description="Универсальный генератор конфигурации")
    parser.add_argument(
        "--show-mapping", action="store_true", help="Показать маппинг env переменных"
    )
    parser.add_argument("--json-file", default="config.json", help="Путь к JSON файлу")
    parser.add_argument(
        "--output", default="client/config/config.py", help="Путь к выходному файлу"
    )

    args = parser.parse_args()

    generator = UniversalConfigGenerator(args.json_file, args.output)

    try:
        generator.load_json_config()
        generator._build_env_mapping(generator.config_data)

        if args.show_mapping:
            generator.print_env_mapping()
            return 0

        generator.generate()
        print("\n🎉 Генерация завершена успешно!")
        print("\nТеперь вы можете:")
        print("1. Использовать .env.generated как основу для .env")
        print("2. Настроить значения в .env файле")
        print("3. Использовать Config.load() в коде")
        print(
            "4. Добавлять новые поля в JSON - они автоматически попадут в конфигурацию!"
        )

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
