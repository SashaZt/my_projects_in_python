import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
from configuration.logger_setup import logger

# Загрузка логина и пароля из .env файла
load_dotenv()
LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")


def login_with_credentials(driver):
    """Автоматичний вхід на сайт за логіном і паролем."""
    driver.get("https://clash.gg/raffle")
    time.sleep(5)  # Чекаємо завантаження сторінки

    # Натискаємо на кнопку "Sign in"
    sign_in_button = driver.find_element(
        By.XPATH,
        '//*[@id="__next"]/div[2]/div[1]/header[2]/div[2]/div/div/div[2]/a[2]/button',
    )
    sign_in_button.click()
    time.sleep(4)  # Чекаємо відкриття меню входу

    # Вводимо логін
    login_field = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="headlessui-tabs-panel-:rb:"]/form/label[1]/input')
        )
    )
    time.sleep(2)
    login_field.send_keys(LOGIN)  # Вводимо логін
    time.sleep(9)  # Чекаємо перед введенням пароля

    # Вводимо пароль
    password_field = driver.find_element(
        By.XPATH, '//*[@id="headlessui-tabs-panel-:rb:"]/form/label[2]/input'
    )
    time.sleep(2)
    password_field.send_keys(PASSWORD)  # Вводимо пароль
    time.sleep(9)  # Затримка перед натисканням кнопки входу

    # Натискаємо на кнопку "Увійти"
    submit_button = driver.find_element(
        By.XPATH, '//*[@id="headlessui-tabs-panel-:rb:"]/form/button[2]'
    )
    time.sleep(2)
    submit_button.click()
    time.sleep(5)
    driver.refresh()
    time.sleep(5)

    print("Успішний вхід.")


def place_bet(driver, bet_amount):
    """Вводимо білети та натискаємо кнопку 'поставити'"""
    try:
        # Знаходимо поле для введення кількості білетів
        bet_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="general-portal"]/div/div[2]/div[2]/div/div/input')
            )
        )
        bet_input.clear()
        bet_input.send_keys(str(bet_amount))
        logger.info(f"Введено {bet_amount} білетів.")

        # Додаємо перевірку, щоб переконатися, що кількість білетів була введена
        WebDriverWait(driver, 5).until(
            lambda d: bet_input.get_attribute("value") == str(bet_amount)
        )

        time.sleep(1)

        # Натискаємо кнопку "поставити"
        final_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="general-portal"]/div/div[2]/button')
            )
        )
        time.sleep(1)
        final_button.click()
        logger.info(f"Ставка на {bet_amount} білетів успішно підтверджена.")

        # Чекаємо, поки кнопка зникне або зміниться, щоб підтвердити, що ставка зроблена
        WebDriverWait(driver, 10).until(EC.staleness_of(final_button))
        logger.info("Ставка підтверджена та оброблена.")

        # Чекаємо 3 хвилини перед перезавантаженням сторінки
        logger.info("Чекаємо 180 секунд перед наступною спробою.")
        time.sleep(180)

    except Exception as e:
        logger.error(f"Помилка під час введення ставки: {e}")


def select_raffle_with_least_time(driver):
    """Обираємо лот з найменшим часом і чекаємо до секунд перед його завершенням"""
    while True:
        try:
            driver.refresh()
            raffle_items = driver.find_elements(
                By.XPATH, '//*[@id="content"]/div/main/div/div[3]/div[1]/div/div/div'
            )
            min_time = float("inf")
            selected_item = None

            for i, item in enumerate(raffle_items):
                try:
                    timer_xpath = f'//*[@id="content"]/div/main/div/div[3]/div[1]/div/div/div[{i + 1}]/div/div[1]/div[2]/span'
                    timer_text = driver.find_element(By.XPATH, timer_xpath).text
                    minutes, seconds = map(int, timer_text.split(":"))
                    remaining_time = minutes * 60 + seconds

                    if remaining_time < min_time:
                        min_time = remaining_time
                        selected_item = i + 1
                except Exception as e:
                    logger.error(f"Помилка з лотом {i + 1}: {e}")

            if selected_item:
                raffle_item_xpath = f'//*[@id="content"]/div/main/div/div[3]/div[1]/div/div/div[{selected_item}]/button'
                driver.find_element(By.XPATH, raffle_item_xpath).click()
                time.sleep(3)

                while min_time > 15:
                    timer_xpath = (
                        '//*[@id="general-portal"]/div/div[2]/div[1]/div[1]/div[2]/span'
                    )
                    timer_text = driver.find_element(By.XPATH, timer_xpath).text
                    minutes, seconds = map(int, timer_text.split(":"))
                    min_time = minutes * 60 + seconds
                    # print(f"Залишилося {min_time} секунд до завершення лоту.")
                    time.sleep(3)

                logger.info("Час менше ніж секунд. Вводимо білети.")
                entries_xpath = (
                    '//*[@id="general-portal"]/div/div[2]/div[1]/div[1]/div[1]/span'
                )
                price_xpath = (
                    '//*[@id="general-portal"]/div/div[2]/div[1]/div[2]/div[2]/span'
                )

                entries = int(
                    driver.find_element(By.XPATH, entries_xpath).text.replace(",", "")
                )
                price = float(
                    driver.find_element(By.XPATH, price_xpath).text.replace(",", "")
                )

                if 0 <= price <= 10:
                    if entries > 2000:
                        logger.warning("Не ставить для зброї з ціною 0-10 монет")
                    elif entries > 1300:
                        place_bet(driver, 500)
                    elif entries > 1:
                        place_bet(driver, 900)
                elif 10 < price <= 40:
                    if entries > 7200:
                        logger.warning("Не ставить для зброї з ціною 10-40 монет")
                    elif entries > 5500:
                        place_bet(driver, 800)
                    elif entries > 3000:
                        place_bet(driver, 1900)
                    elif entries > 1:
                        place_bet(driver, 2300)
                elif 40 < price <= 150:
                    if entries > 25000:
                        logger.warning("Не ставить для зброї з ціною 40-150 монет")
                    elif entries > 22000:
                        place_bet(driver, 2000)
                    elif entries > 14000:
                        place_bet(driver, 4500)
                    elif entries > 1:
                        place_bet(driver, 7000)

        except Exception as e:
            logger.error(f"Помилка під час вибору лота: {e}")


def main():
    driver = webdriver.Chrome()
    try:
        login_with_credentials(driver)
        select_raffle_with_least_time(driver)
    except Exception as e:
        logger.error(f"Сталася помилка: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
