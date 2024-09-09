from email import message_from_bytes
import email.utils
from pathlib import Path
import re
from pathlib import Path
import imaplib
import email
from email.header import decode_header
from dotenv import dotenv_values
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
import time
import re
import csv


def load_env_variables():
    """Загружает переменные окружения из файла .env в папке configuration."""
    return dotenv_values("configuration/.env")


def create_directory_for_user(email, save_dir):
    """Создает директорию для пользователя, основанную на его email."""
    # Извлекаем имя пользователя до '@'
    username = email.split("@")[0]

    # Формируем путь к новой директории
    user_dir = Path(save_dir) / username

    # Создаем директорию, если она не существует
    user_dir.mkdir(parents=True, exist_ok=True)

    return user_dir


def connect_to_mail_server(imap_server, email_account, email_password):
    """Подключается к почтовому серверу и возвращает объект подключения."""
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(email_account, email_password)
    return mail


# def fetch_emails(mail, sender_email):
#     """Ищет и возвращает все письма от указанного отправителя."""
#     mail.select("inbox")
#     status, messages = mail.search(None, f'(FROM "{sender_email}")')
#     if status == "OK":
#         return messages[0].split()
#     else:
#         return []


def fetch_emails(mail, sender_email):
    """Ищет и возвращает все письма от указанного отправителя с id и сгенерированным именем файла."""
    mail.select("inbox")
    status, messages = mail.search(None, f'(FROM "{sender_email}")')

    email_data = []

    if status == "OK":
        email_ids = messages[0].split()
        for email_id in email_ids:
            # Получаем данные письма
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status == "OK":
                msg = email.message_from_bytes(msg_data[0][1])

                # Извлекаем тему
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()

                # Извлекаем дату и форматируем её
                date_str = msg["Date"]
                date_obj = email.utils.parsedate_to_datetime(date_str)
                formatted_date = date_obj.strftime("%Y_%m_%d")

                # Формируем имя файла
                file_name_mail = f"{email_id.decode('utf-8')}_{formatted_date}.eml"

                # Добавляем информацию о письме в список
                email_data.append(
                    {"id": email_id.decode("utf-8"), "file_name": file_name_mail}
                )

    return email_data


# def fetch_emails_datas(mail, sender_email):
#     """Ищет и возвращает все письма от указанного отправителя с заголовками и метаданными."""
#     mail.select("inbox")
#     status, messages = mail.search(None, f'(FROM "{sender_email}")')

#     email_data = []

#     if status == "OK":
#         email_ids = messages[0].split()
#         for email_id in email_ids:
#             # Получаем данные письма
#             status, msg_data = mail.fetch(email_id, "(RFC822)")
#             if status == "OK":
#                 msg = email.message_from_bytes(msg_data[0][1])

#                 # Извлекаем нужные поля
#                 subject = decode_header(msg["Subject"])[0][0]
#                 if isinstance(subject, bytes):
#                     subject = subject.decode()

#                 date = msg["Date"]
#                 from_email = msg["From"]
#                 to_email = msg["To"]

#                 # Добавляем информацию о письме в список
#                 email_data.append(
#                     {
#                         "id": email_id,
#                         "subject": subject,
#                         "date": date,
#                         "from": from_email,
#                         "to": to_email,
#                     }
#                 )

#     return email_data


# def save_email(mail, email_id, save_dir):
#     """Сохраняет письмо с указанным email_id в директорию save_dir."""
#     status, msg_data = mail.fetch(email_id, "(RFC822)")
#     if status == "OK":
#         msg = email.message_from_bytes(msg_data[0][1])
#         email_subject = decode_header(msg["Subject"])[0][0]
#         if isinstance(email_subject, bytes):
#             email_subject = email_subject.decode()

#         filename = f"{email_subject}_{email_id.decode('utf-8')}.eml"
#         filepath = Path(save_dir) / filename
#         with open(filepath, "wb") as f:
#             f.write(msg_data[0][1])
#         print(f"Сохранено письмо: {filepath}")
#     else:
#         print(f"Ошибка при получении письма с ID {email_id}")


def save_email(mail, email_id, save_dir, file_name_mail):
    """Сохраняет письмо с указанным email_id в директорию save_dir с именем файла."""
    status, msg_data = mail.fetch(email_id, "(RFC822)")
    if status == "OK":
        msg = email.message_from_bytes(msg_data[0][1])

        # Используем сгенерированное имя файла
        filepath = Path(save_dir) / file_name_mail
        with open(filepath, "wb") as f:
            f.write(msg_data[0][1])
        logger.info(f"Сохранено письмо: {filepath}")
    else:
        logger.error(f"Ошибка при получении письма с ID {email_id}")


def extract_clean_text_from_email(email_content):
    """Извлекает и очищает текст из HTML содержимого письма."""
    soup = BeautifulSoup(email_content, "html.parser")

    # Удаляем ненужные теги, такие как <style>, <script>, и комментарии
    for element in soup(["style", "script", "[document]", "head", "title"]):
        element.decompose()

    # Извлекаем текст
    clean_text = soup.get_text(separator=" ").strip()

    return clean_text


def save_clean_text_to_file(clean_text, output_path):
    """Сохраняет чистый текст в указанный файл."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(clean_text)
    logger.info(f"Сохранен текст письма в файл: {output_path}")


def process_emails_in_directory(directory, output_directory):
    """Проходит по всем файлам в директории, извлекает текст и сохраняет его в файл."""
    # Создаем директорию для сохранения текстов, если она не существует
    Path(output_directory).mkdir(parents=True, exist_ok=True)

    for filepath in Path(directory).iterdir():
        if filepath.suffix == ".eml":
            with open(filepath, "r", encoding="utf-8") as f:
                email_content = f.read()

            # Извлекаем чистый текст из письма
            clean_text = extract_clean_text_from_email(email_content)

            # Формируем путь для сохранения текста
            output_filename = f"{filepath.stem}.txt"
            output_path = Path(output_directory) / output_filename

            # Сохраняем чистый текст в файл
            save_clean_text_to_file(clean_text, output_path)


def extract_info_from_email(email_content):
    """Извлекает имя пользователя, сумму и дату из содержимого письма."""
    # Извлекаем дату из заголовка письма
    msg = message_from_bytes(email_content.encode("utf-8"))
    date_tuple = email.utils.parsedate_tz(msg["Date"])
    date_str = email.utils.formatdate(
        email.utils.mktime_tz(date_tuple), localtime=True, usegmt=False
    )

    # Преобразуем дату в нужный формат
    formatted_date = format_email_date(date_str)

    # Шаблон для имени пользователя между 'to' и 'and'
    username_match = re.search(r"to (\w+) and", email_content)
    username = username_match.group(1) if username_match else None

    # Шаблон для суммы между 'and earned' и '!'
    amount_match = re.search(r"and earned \$(\d+\.\d+)!", email_content)
    amount = amount_match.group(1) if amount_match else None

    return username, amount, formatted_date


def process_all_emails(user_directory):
    """Проходит по всем файлам в директории и извлекает данные из каждого."""
    results = []

    # Обходим все файлы в указанной директории
    for file_path in Path(user_directory).glob("*.eml"):
        with open(file_path, "r", encoding="utf-8") as f:
            email_content = f.read()

        # Извлекаем данные из письма
        username, amount, date = extract_info_from_email(email_content)

        if username and amount and date:
            # Добавляем результат в список
            results.append(
                {
                    "file": file_path.name,
                    "username": username,
                    "amount": amount,
                    "date": date,
                }
            )

    return results


def write_to_csv(data_list, output_file):
    """Записывает данные (username, amount и дату) в CSV файл."""
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")

        # Записываем заголовки колонок
        writer.writerow(["username", "amount", "date"])

        # Записываем каждую строку данных
        for data in data_list:
            writer.writerow([data["username"], data["amount"], data["date"]])


def format_email_date(date_str):
    """Преобразует дату из формата 'Thu, 20 Jun 2024 17:22:35 +0300' в '2024_06_20'."""
    # Парсим строку даты в объект datetime
    parsed_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")

    # Форматируем дату в нужный формат
    formatted_date = parsed_date.strftime("%Y_%m_%d")

    return formatted_date


def main():
    env_values = load_env_variables()

    EMAIL_ACCOUNT = env_values["EMAIL_ACCOUNT"]
    EMAIL_PASSWORD = env_values["EMAIL_PASSWORD"]

    pattern_email = r"(?<=@)[\w.-]+"
    domain = re.search(pattern_email, EMAIL_ACCOUNT).group()

    if domain == "outlook.com":
        IMAP_SERVER = "outlook.office365.com"
    elif domain == "gmail.com":
        IMAP_SERVER = "imap.gmail.com"
    else:
        raise ValueError(f"Unknown domain: {domain}")
    logger.info(IMAP_SERVER)
    logger.info(EMAIL_ACCOUNT)
    logger.info(EMAIL_PASSWORD)
    SAVE_DIR = env_values.get("SAVE_DIR", "emails")

    user_directory = create_directory_for_user(EMAIL_ACCOUNT, SAVE_DIR)

    try:
        mail = connect_to_mail_server(IMAP_SERVER, EMAIL_ACCOUNT, EMAIL_PASSWORD)
        logger.info(f"Successfully connected to {IMAP_SERVER}")
    except imaplib.IMAP4.error as e:
        logger.error(f"Ошибка подключения: {e}")
        logger.error(f"Проверьте настройки IMAP для {EMAIL_ACCOUNT}")

        # Проверка для Gmail
        if domain == "gmail.com":
            logger.info(
                "Если вы используете Gmail, убедитесь, что доступ через IMAP включен в настройках вашей учетной записи."
            )
            logger.info(
                "Кроме того, если у вас включена двухфакторная аутентификация (2FA), используйте пароль приложения."
            )

        # Проверка для Outlook
        elif domain == "outlook.com":
            logger.info(
                "Если вы используете Outlook, убедитесь, что IMAP включен. "
                "Также рассмотрите использование пароля приложения, если включена двухфакторная аутентификация (2FA)."
            )

        # Проброс исключения дальше
        raise

    sender_email = "sales@manyvids.com"
    email_ids = fetch_emails(mail, sender_email)
    if email_ids:
        for email in email_ids:
            email_id = email["id"]
            file_name_mail = email["file_name"]
            # Проверяем, существует ли уже файл
            file_path = Path(user_directory) / file_name_mail
            if file_path.exists():
                logger.info(
                    f"Файл {file_name_mail} уже существует. Пропускаем скачивание."
                )
                continue

            # Сохраняем письмо, если файл не существует
            save_email(mail, email_id, user_directory, file_name_mail)
            time.sleep(1)  # Добавляем паузу между скачиваниями
    else:
        logger.error(f"Нет писем от {sender_email}")
    email_data = process_all_emails(user_directory)
    output_csv = "output.csv"

    write_to_csv(email_data, output_csv)
    # # Вывод результатов
    # for data in email_data:
    #     logger.info(f"{data['username']};{data['amount']}")


if __name__ == "__main__":
    main()
