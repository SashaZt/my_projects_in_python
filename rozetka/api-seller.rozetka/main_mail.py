import smtplib
from email.mime.text import MIMEText
from pathlib import Path

from logger import logger
from main_token import load_product_data

# Настройка путей и директорий
current_directory = Path.cwd()
config_directory = current_directory / "config"
config_directory.mkdir(parents=True, exist_ok=True)

# Пути к файлам
config_json_file = config_directory / "config.json"
# Данные для авторизации
config = load_product_data(config_json_file)
SENDER_EMAIL = config["mail"]["sender_email"]
APP_PASSWORD = config["mail"]["app_password"]


def get_send_email(receiver_email, body):
    # Настройки твоего Gmail
    # receiver_email = "a.zinchyk83@gmail.com"  # Кому отправить  письмо
    subject = "Замовлення Роблокс"  # Тема письма
    # body = "Привет! Это тестовое письмо, отправленное через Python."  # Текст письма

    # Создание письма
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email

    # Подключение к серверу Gmail и отправка
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Включение шифрования
        server.login(SENDER_EMAIL, APP_PASSWORD)  # Авторизация с паролем приложения
        server.sendmail(
            SENDER_EMAIL, receiver_email, msg.as_string()
        )  # Отправка письма
        server.quit()  # Закрытие соединения
        logger.info("Письмо успешно отправлено!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
