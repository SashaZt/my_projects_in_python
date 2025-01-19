import os
import time

import pyautogui


def debug_mouse_position():
    """Функция для проверки текущей позиции мыши."""
    print("У вас есть 5 секунд чтобы навести мышь на нужное место...")
    time.sleep(5)
    position = pyautogui.position()
    print(f"Текущие координаты мыши: x={position.x}, y={position.y}")
    return position


def open_and_find_file(directory_path, file_name):
    print(f"Открываем проводник для директории: {directory_path}")

    # Проверяем существование директории
    if not os.path.exists(directory_path):
        print(f"Директория не существует: {directory_path}")
        return

    # Открываем директорию в проводнике
    try:
        os.startfile(directory_path)
    except FileNotFoundError:
        print(f"Не удалось открыть директорию: {directory_path}")
        return

    # Увеличиваем окно проводника на весь экран
    time.sleep(2)
    pyautogui.hotkey("win", "up")  # Максимизируем окно

    # Нажимаем Ctrl + F для поиска
    pyautogui.hotkey("ctrl", "f")
    time.sleep(1)

    # Вводим имя файла
    pyautogui.typewrite(file_name)
    time.sleep(2)  # Ждём завершения поиска

    print(f"Файл {file_name} введён для поиска.")
    print("Теперь наведите мышь на найденный файл...")

    # Получаем реальные координаты
    real_position = debug_mouse_position()

    print("\nПроверка координат:")
    print(f"Сохранённые координаты: {real_position}")

    # Перемещаем мышь в сторону для проверки
    pyautogui.moveTo(100, 100, duration=1)
    time.sleep(1)

    # Возвращаем мышь к файлу
    print(f"Возвращаем мышь на позицию {real_position}")
    pyautogui.moveTo(real_position.x, real_position.y, duration=1)

    return real_position


if __name__ == "__main__":
    directory_path = (
        r"C:\\Temp\\001_Exterior Furniture\\004_exterior_table+chairs+umbrella"
    )
    file_name = "3141052.5fc158ee066f5.jpeg"

    print("=== Начинаем отладку координат ===")
    actual_position = open_and_find_file(directory_path, file_name)

    print(f"\nИспользуем координаты: x={actual_position.x}, y={actual_position.y}")
