#!/usr/bin/env python3
"""
Универсальный генератор конфигураций для Docker Compose
Поддерживает гибкое преобразование JSON в различные форматы
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class OutputFormat(Enum):
    ENV = "env"
    JSON = "json"
    YAML = "yaml"
    DOCKER_ENV = "docker_env"


@dataclass
class ComponentMapping:
    """Конфигурация маппинга для компонента"""

    name: str
    sections: List[str] = field(default_factory=list)
    env_prefix: str = ""
    custom_mappings: Dict[str, str] = field(default_factory=dict)
    exclude_keys: List[str] = field(default_factory=list)
    include_global: bool = True


class ConfigProcessor:
    """Основной класс для обработки конфигураций"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = {}
        self.load_config()

        # Предустановленные маппинги для популярных сервисов
        self.service_mappings = {
            "db": ComponentMapping(
                name="db",
                sections=["db"],
                env_prefix="PG_",
                custom_mappings={
                    "db_user": "POSTGRES_USER",
                    "db_password": "POSTGRES_PASSWORD",
                    "db_name": "POSTGRES_DB",
                    "db_pgdata_path": "PGDATA",
                    "db_host": "POSTGRES_HOST",
                    "db_port": "POSTGRES_PORT",
                },
            ),
            "client": ComponentMapping(
                name="client", sections=["client"], 
            ),
            "api": ComponentMapping(name="api", sections=["api"], env_prefix="API_"),
        }

    def load_config(self) -> None:
        """Загружает конфигурацию из JSON файла"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл конфигурации {self.config_path} не найден")
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON: {e}")

    def flatten_dict(
        self, data: Dict[str, Any], parent_key: str = "", separator: str = "_"
    ) -> Dict[str, Any]:
        """Рекурсивно преобразует вложенную структуру в плоскую"""
        items = []

        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(self.flatten_dict(value, new_key, separator).items())
            elif isinstance(value, list):
                # Сериализуем списки в JSON строку
                items.append((new_key, json.dumps(value)))
            elif isinstance(value, bool):
                # Преобразуем булевы значения в строки
                items.append((new_key, str(value).lower()))
            else:
                items.append((new_key, value))

        return dict(items)

    def clean_env_key(self, key: str) -> str:
        """Очищает ключ для использования в переменных окружения"""
        # Заменяем все недопустимые символы на подчеркивания
        key = re.sub(r"[^A-Za-z0-9_]", "_", key)
        # Убираем множественные подчеркивания
        key = re.sub(r"_+", "_", key)
        # Убираем подчеркивания в начале и конце
        key = key.strip("_")
        return key.upper()

    def escape_env_value(self, value: Any) -> str:
        """Безопасно экранирует значение для .env файла"""
        if not isinstance(value, str):
            return str(value)

        # Экранируем потенциально опасные символы
        value = value.replace("\\", "\\\\")  # Обратные слеши
        value = value.replace('"', '\\"')  # Кавычки
        value = value.replace("$", "\\$")  # Знаки доллара
        value = value.replace("`", "\\`")  # Обратные кавычки

        # Если содержит специальные символы, заключаем в кавычки
        if re.search(r"[\s\[\](){}*?;:&|<>!#]", value):
            return f'"{value}"'

        return value

    def get_component_config(
        self, component: str, custom_mapping: Optional[ComponentMapping] = None
    ) -> Dict[str, Any]:
        """Извлекает конфигурацию для конкретного компонента"""
        mapping = custom_mapping or self.service_mappings.get(component)

        if not mapping:
            # Если маппинг не найден, создаем базовый
            mapping = ComponentMapping(
                name=component, sections=[component], env_prefix=f"{component.upper()}_"
            )

        result = {}

        # Добавляем глобальные настройки
        if mapping.include_global:
            global_keys = ["project"]
            for key in global_keys:
                if key in self.config:
                    result[key] = self.config[key]

        # Добавляем секции компонента
        for section in mapping.sections:
            if section in self.config:
                if isinstance(self.config[section], dict):
                    result[section] = self.config[section]
                else:
                    result[section] = self.config[section]

        return result

    def generate_env_variables(
        self, component_config: Dict[str, Any], mapping: ComponentMapping
    ) -> Dict[str, str]:
        """Генерирует переменные окружения из конфигурации компонента"""
        env_vars = {}
        flat_config = self.flatten_dict(component_config)

        for key, value in flat_config.items():
            # Проверяем исключения
            if key in mapping.exclude_keys:
                continue

            # Применяем кастомные маппинги
            env_key = mapping.custom_mappings.get(key)
            if not env_key:
                # Генерируем стандартное имя переменной
                clean_key = self.clean_env_key(key)
                env_key = (
                    f"{mapping.env_prefix}{clean_key}"
                    if mapping.env_prefix
                    else clean_key
                )

            env_vars[env_key] = self.escape_env_value(value)

        return env_vars

    def write_env_file(
        self, env_vars: Dict[str, str], output_path: str, component: str = ""
    ) -> None:
        """Записывает переменные окружения в .env файл"""
        with open(output_path, "w", encoding="utf-8") as f:
            if component:
                f.write(f"# Configuration for {component.upper()}\n")
                f.write(f"# Generated from {self.config_path}\n\n")

            # Группируем переменные по префиксам
            grouped_vars = {}
            for key, value in env_vars.items():
                prefix = key.split("_")[0] if "_" in key else "OTHER"
                if prefix not in grouped_vars:
                    grouped_vars[prefix] = {}
                grouped_vars[prefix][key] = value

            # Записываем переменные группами
            for prefix in sorted(grouped_vars.keys()):
                if prefix != "OTHER":
                    f.write(f"# {prefix} Configuration\n")

                for key in sorted(grouped_vars[prefix].keys()):
                    f.write(f"{key}={grouped_vars[prefix][key]}\n")

                f.write("\n")

    def write_json_file(self, config: Dict[str, Any], output_path: str) -> None:
        """Записывает конфигурацию в JSON файл"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def generate_component_config(
        self,
        component: str,
        output_format: OutputFormat = OutputFormat.ENV,
        output_dir: Optional[str] = None,
        custom_mapping: Optional[ComponentMapping] = None,
    ) -> bool:
        """Генерирует конфигурацию для компонента"""
        try:
            # Получаем конфигурацию компонента
            component_config = self.get_component_config(component, custom_mapping)
            mapping = custom_mapping or self.service_mappings.get(
                component, ComponentMapping(name=component)
            )

            # Определяем путь вывода
            if output_dir is None:
                output_dir = f"./{component}"

            os.makedirs(output_dir, exist_ok=True)

            if output_format == OutputFormat.ENV:
                env_vars = self.generate_env_variables(component_config, mapping)
                output_path = os.path.join(output_dir, ".env")
                self.write_env_file(env_vars, output_path, component)
            print(f"✅ Конфигурация для {component} сгенерирована: {output_path}")
            return True

        except Exception as e:
            print(f"❌ Ошибка при генерации конфигурации для {component}: {e}")
            return False

    def generate_main_env(self, output_file: str = ".env") -> bool:
        """Генерирует основной .env файл со всеми переменными"""
        try:
            all_env_vars = {}

            # Сначала добавляем глобальные переменные
            global_keys = ["project"]
            for key in global_keys:
                if key in self.config:
                    if isinstance(self.config[key], dict):
                        flat_global = self.flatten_dict({key: self.config[key]})
                        for gkey, gvalue in flat_global.items():
                            env_key = self.clean_env_key(gkey)
                            all_env_vars[env_key] = self.escape_env_value(gvalue)
                    else:
                        env_key = self.clean_env_key(key)
                        all_env_vars[env_key] = self.escape_env_value(self.config[key])

            # Генерируем переменные для всех известных сервисов
            for service_name, mapping in self.service_mappings.items():
                if any(section in self.config for section in mapping.sections):
                    component_config = self.get_component_config(service_name, mapping)
                    env_vars = self.generate_env_variables(component_config, mapping)
                    all_env_vars.update(env_vars)

            # Добавляем остальные секции, которые не обработаны маппингами
            processed_sections = set()
            for mapping in self.service_mappings.values():
                processed_sections.update(mapping.sections)

            remaining_sections = {
                k: v
                for k, v in self.config.items()
                if k not in processed_sections
                and k not in ["project"]
                and isinstance(v, dict)
            }

            if remaining_sections:
                flat_remaining = self.flatten_dict(remaining_sections)
                for key, value in flat_remaining.items():
                    env_key = self.clean_env_key(key)
                    all_env_vars[env_key] = self.escape_env_value(value)

            self.write_env_file(all_env_vars, output_file)
            print(f"✅ Основной .env файл сгенерирован: {output_file}")
            print(f"📊 Всего переменных: {len(all_env_vars)}")

            # Показываем группировку переменных
            postgres_vars = [
                k for k in all_env_vars.keys() if k.startswith(("POSTGRES_", "PG_"))
            ]
            client_vars = [k for k in all_env_vars.keys() if k.startswith("CLIENT_")]
            global_vars = [
                k
                for k in all_env_vars.keys()
                if k
                in [
                    "PROJECT_NAME",
                    "PROJECT_VERSION",
                    "PROJECT_ENVIRONMENT",
                    "PROJECT_TIMEZONE",
                ]
            ]

            print(f"   🗄️  PostgreSQL: {len(postgres_vars)} переменных")
            print(f"   🔧 Client: {len(client_vars)} переменных")
            print(f"   🌐 Глобальные: {len(global_vars)} переменных")

            return True

        except Exception as e:
            print(f"❌ Ошибка при генерации основного .env файла: {e}")
            return False

    def generate_service_env_files(self) -> bool:
        """Генерирует .env.{service} файлы для каждого сервиса с их специфичными переменными"""
        try:
            for service_name, mapping in self.service_mappings.items():
                if any(section in self.config for section in mapping.sections):
                    component_config = self.get_component_config(service_name, mapping)
                    env_vars = self.generate_env_variables(component_config, mapping)

                    # Фильтруем только переменные, специфичные для этого сервиса
                    service_specific_vars = {}

                    if service_name in ["db"]:
                        # Для PostgreSQL берем только PG_ переменные и основные POSTGRES_
                        for key, value in env_vars.items():
                            service_specific_vars[key] = value
                    elif service_name == "client":
                        # Для Client берем CLIENT_ переменные
                        for key, value in env_vars.items():
                            if key.startswith("CLIENT_"):
                                service_specific_vars[key] = value
                    else:
                        # Для других сервисов берем переменные с их префиксом
                        prefix = f"{service_name.upper()}_"
                        for key, value in env_vars.items():
                            if key.startswith(prefix):
                                service_specific_vars[key] = value

                    if service_specific_vars:
                        output_file = f".env.{service_name}"
                        self.write_env_file(
                            service_specific_vars, output_file, service_name
                        )
                        print(
                            f"✅ Сервис-специфичный файл создан: {output_file} ({len(service_specific_vars)} переменных)"
                        )

            return True

        except Exception as e:
            print(f"❌ Ошибка при генерации сервис-специфичных .env файлов: {e}")
            return False

    def create_service_directories(self) -> bool:
        """Создает директории для сервисов если они не существуют"""
        try:
            services_to_check = ["db", "client", "api"]
            created_dirs = []

            for service in services_to_check:
                if service in self.config:
                    service_dir = f"./{service}"
                    if not os.path.exists(service_dir):
                        os.makedirs(service_dir, exist_ok=True)
                        created_dirs.append(service_dir)
                        print(f"📁 Создана директория: {service_dir}")
                    else:
                        print(f"✅ Директория уже существует: {service_dir}")

            if created_dirs:
                print(f"📋 Создано директорий: {len(created_dirs)}")

            return True

        except Exception as e:
            print(f"❌ Ошибка при создании директорий: {e}")
            return False

    def show_available_components(self) -> None:
        """Показывает доступные компоненты в конфигурации"""
        print("🔍 Доступные компоненты в конфигурации:")
        print(f"   Файл: {self.config_path}")
        print()

        # Глобальные параметры (project)
        if "project" in self.config and isinstance(self.config["project"], dict):
            print("📋 Глобальные параметры (project):")
            for key, value in self.config["project"].items():
                print(f"   • {key}: {value}")
            print()

        # Секции компонентов
        component_sections = [
            k
            for k in self.config.keys()
            if isinstance(self.config[k], dict) and k != "project"
        ]
        if component_sections:
            print("🔧 Секции компонентов:")
            for section in component_sections:
                items_count = (
                    len(self.config[section])
                    if isinstance(self.config[section], dict)
                    else 1
                )
                # Проверяем существование директории
                dir_status = "📁" if os.path.exists(f"./{section}") else "❌"
                print(f"   {dir_status} {section} ({items_count} параметров)")
            print()

        # Предустановленные маппинги
        print("⚙️  Предустановленные маппинги:")
        for name, mapping in self.service_mappings.items():
            available = any(section in self.config for section in mapping.sections)
            status = "✅" if available else "❌"
            print(f"   {status} {name} -> {mapping.sections}")


def main():
    """Основная функция CLI"""
    if len(sys.argv) < 2:
        print("🚀 Универсальный генератор конфигураций")
        print()
        print("Использование:")
        print("  python config_loader.py <команда> [параметры]")
        print()
        print("Команды:")
        print("  show                          - показать доступные компоненты")
        print("  create-dirs                   - создать директории для сервисов")
        print("  generate-main [output.env]    - сгенерировать основной .env файл")
        print("  generate-component <name>     - сгенерировать конфигурацию компонента")
        print("  generate-service-envs         - сгенерировать .env.{service} файлы")
        print("  generate-all                  - сгенерировать все конфигурации")
        print()
        print("Параметры для generate-component:")
        print("  --format env|json|docker_env  - формат вывода (по умолчанию: env)")
        print("  --output <dir>                - директория вывода")
        print("  --config <path>               - путь к config.json")
        return

    command = sys.argv[1]
    config_path = "config.json"

    # Поиск параметра --config
    if "--config" in sys.argv:
        idx = sys.argv.index("--config")
        if idx + 1 < len(sys.argv):
            config_path = sys.argv[idx + 1]

    try:
        processor = ConfigProcessor(config_path)

        if command == "show":
            processor.show_available_components()

        elif command == "create-dirs":
            processor.create_service_directories()

        elif command == "generate-main":
            output_file = (
                sys.argv[2]
                if len(sys.argv) > 2 and not sys.argv[2].startswith("--")
                else ".env"
            )
            processor.generate_main_env(output_file)

        elif command == "generate-component":
            if len(sys.argv) < 3:
                print("❌ Необходимо указать имя компонента")
                return

            component = sys.argv[2]
            output_format = OutputFormat.ENV
            output_dir = None

            # Парсим дополнительные параметры
            if "--format" in sys.argv:
                idx = sys.argv.index("--format")
                if idx + 1 < len(sys.argv):
                    format_str = sys.argv[idx + 1]
                    try:
                        output_format = OutputFormat(format_str)
                    except ValueError:
                        print(f"❌ Неизвестный формат: {format_str}")
                        return

            if "--output" in sys.argv:
                idx = sys.argv.index("--output")
                if idx + 1 < len(sys.argv):
                    output_dir = sys.argv[idx + 1]

            processor.generate_component_config(component, output_format, output_dir)

        elif command == "generate-service-envs":
            processor.generate_service_env_files()

        elif command == "generate-all":
            print("🔄 Генерация всех конфигураций...")

            # Создаем директории если их нет
            processor.create_service_directories()

            # Генерируем основной .env
            processor.generate_main_env()

            # Генерируем сервис-специфичные .env файлы
            # processor.generate_service_env_files()

            # Генерируем конфигурации для всех доступных компонентов в их директории
            for component_name in processor.service_mappings.keys():
                mapping = processor.service_mappings[component_name]
                if any(section in processor.config for section in mapping.sections):
                    processor.generate_component_config(
                        component_name, OutputFormat.ENV
                    )
                    processor.generate_component_config(
                        component_name, OutputFormat.JSON
                    )

            print("✅ Все конфигурации сгенерированы!")

        else:
            print(f"❌ Неизвестная команда: {command}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


# Для обратной совместимости
def generate_component_config(
    component="db", output_format="env", config_path="config.json"
):
    """Функция для обратной совместимости с существующими скриптами"""
    processor = ConfigProcessor(config_path)
    format_enum = OutputFormat.ENV if output_format == "env" else OutputFormat.JSON
    return processor.generate_component_config(component, format_enum)


if __name__ == "__main__":
    main()
