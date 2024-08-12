import pyautogui
import time


# Задержка между действиями
pyautogui.PAUSE = 2

# Подождать 3 секунды перед началом
pyautogui.sleep(3)


def find_and_click(image_path):
    # Найти элемент на экране
    location = pyautogui.locateOnScreen(image_path, confidence=0.8)

    if location is not None:
        # Получить центр найденного элемента
        center = pyautogui.center(location)

        # Переместить курсор и кликнуть на элемент
        pyautogui.moveTo(center)
        pyautogui.click()

        # Переместиться на указанные координаты X=1293, Y=942
        pyautogui.moveTo(918, 1052)

        # Выполнить тройной клик
        pyautogui.tripleClick()

        # Выполнить сочетание клавиш Ctrl+C
        pyautogui.hotkey("ctrl", "c")

        print("Элемент найден и обработан.")
    else:
        print("Элемент не найден на экране.")


def get_mouse_position():
    # Получаем текущие координаты курсора
    x, y = pyautogui.position()

    # Очищаем строку и выводим координаты
    print(f"Текущие координаты мыши: X={x}, Y={y}", end="\r")

    # Задержка перед обновлением


if __name__ == "__main__":
    # Задержка между действиями
    pyautogui.PAUSE = 2

    # Подождать 3 секунды перед началом
    # pyautogui.sleep(1)

    # Путь к изображению
    image_path = r"C:\my_projects_in_python\Viber\viber.png"

    find_and_click(image_path)

    # get_mouse_position()
