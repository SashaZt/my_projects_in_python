# ./config_loader.py
"""
Скрипт для генерации переменных окружения из config.json для Docker Compose
"""

import json
import os
import sys


def flatten_json(json_obj, parent_key="", separator="_"):
    """
    Рекурсивно преобразует вложенную структуру JSON в плоскую с префиксами
    """
    items = []
    for key, value in json_obj.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key.upper()

        if isinstance(value, dict):
            items.extend(flatten_json(value, new_key, separator).items())
        else:
            # Обработка булевых значений и списков
            if isinstance(value, bool):
                value = str(value).lower()
            elif isinstance(value, list):
                value = json.dumps(value)

            items.append((new_key.upper(), value))

    return dict(items)


def generate_env_file(config_path="config.json", output_file=".env"):
    """
    Генерирует .env файл на основе config.json для использования с docker-compose
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Преобразование JSON в плоскую структуру
        flat_config = flatten_json(config)
        # Запись в .env файл
        with open(output_file, "w", encoding="utf-8") as f:
            for key, value in flat_config.items():
                # Пропускаем ключи с точками, так как они вызывают проблемы
                if "." in key:
                    key = key.replace(".", "_")

                # Экранируем значения со специальными символами
                if isinstance(value, str):
                    if any(c in value for c in "[](){}*? \t\n;:$&|<>"):
                        value = f"'{value}'"

                f.write(f"{key}={value}\n")

        print(f"Успешно сгенерирован файл {output_file} из {config_path}")
        return True

    except Exception as e:
        print(f"Ошибка при генерации .env файла: {e}")
        return False


def generate_component_config(
    config_path="config.json", component="bot", output_format="json"
):
    """
    Генерирует конфигурацию для определенного компонента системы
    и помещает её в директорию компонента
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Базовая конфигурация - общие настройки
        component_config = {
            "project_name": config.get("project_name", ""),
            "version": config.get("version", ""),
            "environment": config.get("environment", ""),
            "timezone": config.get("timezone", ""),
        }

        # Добавление специфических настроек для компонента
        if component == "client":
            component_config.update({"client": config.get("client", {})})

        # Определяем путь к директории компонента
        component_dir = f"./{component}"

        # Проверяем существование директории
        if not os.path.exists(component_dir):
            print(f"Предупреждение: Директория {component_dir} не найдена!")
            # Можно создать директорию, но лучше предупредить
            # os.makedirs(component_dir, exist_ok=True)

        # Вывод в нужный формат
        if output_format == "json":
            output_file = f"{component_dir}/{component}_config.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(component_config, f, indent=4)
        elif output_format == "env":
            output_file = f"{component_dir}/.env"
            flat_config = flatten_json(component_config)
            with open(output_file, "w", encoding="utf-8") as f:
                for key, value in flat_config.items():
                    if "." in key:
                        key = key.replace(".", "_")
                    if isinstance(value, str):
                        if any(c in value for c in "[](){}*? \t\n;:$&|<>"):
                            value = f"'{value}'"
                    f.write(f"{key}={value}\n")

        print(
            f"Успешно сгенерирована конфигурация для {component} в формате {output_format} в {output_file}"
        )
        return True

    except Exception as e:
        print(f"Ошибка при генерации конфигурации для {component}: {e}")
        return False


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else ".env"

    success = generate_env_file(config_path, output_file)
    sys.exit(0 if success else 1)
