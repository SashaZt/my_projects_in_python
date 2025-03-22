# ebay_cli.py
"""
Командный интерфейс для работы с API eBay.
Объединяет различные функции для работы с местоположениями, товарами и предложениями.
"""

import json
import os
import sys

from location_management import create_sample_location, get_locations
from logger import logger
from upload_item import upload_product_to_ebay


def clear_screen():
    """Очистка экрана консоли"""
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    """Вывод заголовка приложения"""
    print("=" * 60)
    print("                   API eBay INTEGRATION CLI")
    print("=" * 60)
    print("Версия 1.0 | Разработка: 2025")
    print("-" * 60)


def print_menu():
    """Вывод основного меню"""
    print("\nМЕНЮ:")
    print("1. Управление местоположениями")
    print("2. Управление товарами")
    print("3. Проверка конфигурации")
    print("0. Выход")


def location_menu():
    """Меню управления местоположениями"""
    while True:
        clear_screen()
        print_header()
        print("\nУПРАВЛЕНИЕ МЕСТОПОЛОЖЕНИЯМИ:")
        print("1. Получить список местоположений")
        print("2. Создать новое местоположение")
        print("0. Вернуться в главное меню")

        choice = input("\nВыберите действие: ")

        if choice == "1":
            print("\nПолучение списка местоположений...")
            locations = get_locations()

            if locations:
                print(f"\nНайдено {len(locations)} местоположений.")

                for idx, location in enumerate(locations, 1):
                    merchant_key = location.get("merchantLocationKey", "N/A")
                    name = location.get("location", {}).get("name", "N/A")
                    status = location.get("location", {}).get(
                        "merchantLocationStatus", "N/A"
                    )

                    print(f"\n=== Местоположение #{idx} ===")
                    print(f"Ключ: {merchant_key}")
                    print(f"Имя: {name}")
                    print(f"Статус: {status}")

                # Запись ключей местоположений в файл для облегчения настройки
                with open("location_keys.txt", "w", encoding="utf-8") as f:
                    for location in locations:
                        merchant_key = location.get("merchantLocationKey", "")
                        name = location.get("location", {}).get("name", "")
                        f.write(f"{merchant_key} - {name}\n")

                print("\nКлючи местоположений сохранены в файл location_keys.txt")

            input("\nНажмите Enter для продолжения...")

        elif choice == "2":
            print("\nСоздание нового местоположения...")
            result = create_sample_location()

            if result:
                print("\nМестоположение успешно создано!")
                print("Не забудьте обновить MERCHANT_LOCATION_KEY в файле config.py")
            else:
                print("\nНе удалось создать местоположение.")

            input("\nНажмите Enter для продолжения...")

        elif choice == "0":
            break

        else:
            print("Неверный выбор. Попробуйте снова.")
            input("\nНажмите Enter для продолжения...")


def product_menu():
    """Меню управления товарами"""
    while True:
        clear_screen()
        print_header()
        print("\nУПРАВЛЕНИЕ ТОВАРАМИ:")
        print("1. Загрузить товар из файла")
        print("2. Создать новый шаблон товара")
        print("3. Просмотреть доступные шаблоны")
        print("0. Вернуться в главное меню")

        choice = input("\nВыберите действие: ")

        if choice == "1":
            print("\nДоступные шаблоны товаров:")

            # Поиск JSON-файлов в текущей директории
            json_files = [
                f for f in os.listdir(".") if f.endswith(".json") and f != "config.json"
            ]

            if not json_files:
                print("Шаблоны товаров не найдены.")
                input("\nНажмите Enter для продолжения...")
                continue

            for idx, file in enumerate(json_files, 1):
                print(f"{idx}. {file}")

            file_idx = input("\nВыберите номер файла (0 для отмены): ")

            if file_idx == "0":
                continue

            try:
                file_name = json_files[int(file_idx) - 1]
                print(f"\nЗагрузка товара из файла {file_name}...")

                result = upload_product_to_ebay(file_name)

                if result:
                    print("\nТовар успешно загружен на eBay!")
                else:
                    print("\nНе удалось загрузить товар на eBay.")

            except (ValueError, IndexError):
                print("Неверный выбор файла.")

            input("\nНажмите Enter для продолжения...")

        elif choice == "2":
            print("\nСоздание нового шаблона товара")
            template_name = input("Введите имя файла шаблона (без расширения): ")

            if not template_name:
                print("Имя файла не может быть пустым.")
                input("\nНажмите Enter для продолжения...")
                continue

            file_name = f"{template_name}.json"

            # Базовый шаблон товара
            template = {
                "sku": f"{template_name.upper()}-{int(time.time())}",
                "title": "Новый товар",
                "description": "<p>Описание товара</p>",
                "category_id": "177",
                "price": {"value": 99.99, "currency": "EUR"},
                "quantity": 1,
                "condition": "USED_EXCELLENT",
                "condition_description": "Описание состояния",
                "aspects": {"Brand": ["Бренд"], "Model": ["Модель"]},
                "images": ["https://example.com/image.jpg"],
                "listing_policies": {
                    "best_offer_enabled": False,
                    "listing_duration": "GTC",
                },
            }

            try:
                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump(template, f, ensure_ascii=False, indent=2)

                print(f"\nШаблон товара успешно создан: {file_name}")
                print("Отредактируйте файл перед загрузкой товара.")

            except Exception as e:
                print(f"\nОшибка при создании шаблона: {e}")

            input("\nНажмите Enter для продолжения...")

        elif choice == "3":
            print("\nДоступные шаблоны товаров:")

            # Поиск JSON-файлов в текущей директории
            json_files = [
                f for f in os.listdir(".") if f.endswith(".json") and f != "config.json"
            ]

            if not json_files:
                print("Шаблоны товаров не найдены.")
            else:
                for idx, file in enumerate(json_files, 1):
                    # Пытаемся получить название товара из файла
                    try:
                        with open(file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            title = data.get("title", "Название не указано")
                    except:
                        title = "Ошибка чтения файла"

                    print(f"{idx}. {file} - {title}")

            input("\nНажмите Enter для продолжения...")

        elif choice == "0":
            break

        else:
            print("Неверный выбор. Попробуйте снова.")
            input("\nНажмите Enter для продолжения...")


def check_configuration():
    """Проверка конфигурации приложения"""
    clear_screen()
    print_header()
    print("\nПРОВЕРКА КОНФИГУРАЦИИ:")

    from config import (
        BASE_URL,
        CLIENT_ID,
        CLIENT_SECRET,
        MERCHANT_LOCATION_KEY,
        PAYMENT_POLICY_ID,
        RETURN_POLICY_ID,
        SANDBOX_MODE,
        SHIPPING_POLICY_ID,
    )

    print(f"\nРежим работы: {'Песочница (Sandbox)' if SANDBOX_MODE else 'Продакшн'}")
    print(f"Базовый URL: {BASE_URL}")

    # Проверка учетных данных
    if CLIENT_ID and CLIENT_SECRET:
        print("Учетные данные API: ✓ Настроены")
    else:
        print("Учетные данные API: ✗ Не настроены")

    # Проверка местоположения
    if MERCHANT_LOCATION_KEY:
        print(f"Местоположение продавца: ✓ Настроено ({MERCHANT_LOCATION_KEY})")
    else:
        print("Местоположение продавца: ✗ Не настроено")

    # Проверка политик
    policies_configured = all([PAYMENT_POLICY_ID, RETURN_POLICY_ID, SHIPPING_POLICY_ID])
    if policies_configured:
        print("Политики продавца: ✓ Настроены")
    else:
        print("Политики продавца: ✗ Настроены не полностью")

    # Проверка файлов токенов
    token_file = "config/tokens.json"
    if os.path.exists(token_file):
        print("Файл токенов: ✓ Существует")
    else:
        print("Файл токенов: ✗ Отсутствует")

    input("\nНажмите Enter для возврата в меню...")


def main():
    """Основная функция CLI"""
    import time

    while True:
        clear_screen()
        print_header()
        print_menu()

        choice = input("\nВыберите действие: ")

        if choice == "1":
            location_menu()

        elif choice == "2":
            product_menu()

        elif choice == "3":
            check_configuration()

        elif choice == "0":
            print("\nЗавершение работы...")
            time.sleep(1)
            sys.exit(0)

        else:
            print("Неверный выбор. Попробуйте снова.")
            input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nРабота программы прервана пользователем.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        print(f"\nПроизошла ошибка: {e}")
        print("Подробности смотрите в логах.")
        sys.exit(1)
