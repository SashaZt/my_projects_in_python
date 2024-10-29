from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import re
import os
from dotenv import load_dotenv

chrome_profile_path = "C:/Users/rushw/AppData/Local/Google/Chrome/User Data/Profile 1"
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Загрузка логина и пароля из .env файла
load_dotenv()
LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")


def place_bet(driver, bet_amount):
    # Введення кількості білетів
    bet_click = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "/html/body/div[2]/div[1]/div/div/div[4]/div[2]/div/div[1]/div[1]/div[2]/button",
            )
        )
    )
    bet_click.click()

    time.sleep(2)
    bet_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div[2]/div[4]/div"))
    )

    driver.execute_script(
        "arguments[0].value = arguments[1];", bet_input, str(bet_amount)
    )
    time.sleep(2)

    # Натискання на кнопку 'Enter with X'
    enter_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div[2]/button"))
    )
    enter_button.click()

    print(f"Ставка {bet_amount} білетів зроблена.")


def monitor_and_bet(driver):

    driver.refresh()
    time.sleep(3)
    raffle_items = driver.find_elements(
        By.XPATH,
        "/html/body/div[2]/div[1]/div/div/div[4]/div[2]/div/div[1]/div[1]/div[1]/span",
    )
    print("3")

    for item in raffle_items:
        # Отримати час до закінчення
        timer_text = item.find_element(
            By.XPATH,
            "/html/body/div[2]/div[1]/div/div/div[4]/div[2]/div/div[1]/div[2]/div",
        ).text
        # Перевірити, чи timer_text не пустий
        if timer_text:
            minutes, seconds = map(int, timer_text.split(":"))
            remaining_time = minutes * 60 + seconds
            print(remaining_time)
        else:
            print("Помилка: Таймер не має значення.")
            continue

        # Отримуємо кількість Entries та ціну зброї
        entries_text = item.find_element(
            By.XPATH,
            "/html/body/div[2]/div[1]/div/div/div[4]/div[2]/div/div[1]/div[1]/div[2]/div/div/span",
        ).text
        entries = int(entries_text)
        print(entries)

        price_element = driver.find_element(
            By.XPATH,
            "/html/body/div[2]/div[1]/div/div/div[4]/div[2]/div/div[1]/div[1]/div[1]/div[2]",
        )

        # Отримати текст з елемента
        price_text = price_element.text
        print(f"Повний текст: {price_text}")
        number_match = re.search(r"\d+", price_text)
        if number_match:
            number = int(number_match.group(0))
            print(f"Витягнуте число: {number}")

        print("6")

        # Логіка для визначення кількості білетів в залежності від Entries та ціни
        if 10 <= remaining_time <= 30:  # якщо залишилося 30 секунд
            if 0 <= number <= 25:
                if entries > 4300:
                    print("Не ставить для зброї з ціною 0-25 монет")
                elif entries > 3300:
                    place_bet(driver, 700)
                elif entries > 2000:
                    place_bet(driver, 1100)
                elif entries > 1:
                    place_bet(driver, 1600)
            elif 25 < number <= 70:
                if entries > 14000:
                    print("Не ставить для зброї з ціною 25-70 монет")
                elif entries > 11000:
                    place_bet(driver, 1500)
                elif entries > 9000:
                    place_bet(driver, 2500)
                elif entries > 6000:
                    place_bet(driver, 4000)
                elif entries > 1:
                    place_bet(driver, 5000)
            elif 71 < number <= 120:
                if entries > 42000:
                    print("Не ставить для зброї з ціною 71-120 монет")
                elif entries > 37500:
                    place_bet(driver, 3500)
                elif entries > 32000:
                    place_bet(driver, 6500)
                elif entries > 20000:
                    place_bet(driver, 11500)
                elif entries > 1:
                    place_bet(driver, 14000)


def main():
    # Створюємо драйвер з профілем
    driver = webdriver.Chrome()
    # Завантажуємо сторінку
    driver.get("https://cases.gg/")
    time.sleep(3)

    element = driver.find_element(By.CSS_SELECTOR, "button[data-id='sign_in']")
    driver.execute_script("arguments[0].click();", element)
    time.sleep(4)
    email = driver.find_element(
        By.XPATH, "/html/body/div[5]/div[3]/div/div/form/fieldset/div[1]/input"
    )
    email.clear()
    email.send_keys(LOGIN)
    password = driver.find_element(
        By.XPATH, "/html/body/div[5]/div[3]/div/div/form/fieldset/div[2]/div[2]/input"
    )
    password.clear()
    password.send_keys(PASSWORD)
    time.sleep(5)
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[@type='submit' and .//div[text()='Sign in']]")
        )
    )

    # Нажимаем на элемент через JavaScript
    driver.execute_script("arguments[0].click();", element)
    time.sleep(10)

    driver.get("https://cases.gg/raffles")
    while True:
        monitor_and_bet(driver)


if __name__ == "__main__":
    main()
