import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


def load_env_variables():
    """Загружает переменные окружения из .env файла."""
    load_dotenv()


def create_directory(directory):
    """Создает директорию, если она не существует."""
    os.makedirs(directory, exist_ok=True)


def connect_to_mail_server(imap_server, email_account, email_password):
    """Подключается к почтовому серверу и возвращает объект подключения."""
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(email_account, email_password)
    return mail


def fetch_emails(mail, sender_email, days=3):
    """Ищет и возвращает письма от указанного отправителя за последние 'days' дней."""
    date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
    mail.select("inbox")
    status, messages = mail.search(None, f'(SINCE {date} FROM "{sender_email}")')
    if status == "OK":
        return messages[0].split()
    else:
        return []


def save_email(mail, email_id, save_dir):
    """Сохраняет письмо с указанным email_id в директорию save_dir."""
    status, msg_data = mail.fetch(email_id, "(RFC822)")
    if status == "OK":
        msg = email.message_from_bytes(msg_data[0][1])
        email_subject = decode_header(msg["Subject"])[0][0]
        if isinstance(email_subject, bytes):
            email_subject = email_subject.decode()

        filename = f"{email_subject}_{email_id.decode('utf-8')}.eml"
        filepath = os.path.join(save_dir, filename)
        with open(filepath, "wb") as f:
            f.write(msg_data[0][1])
        print(f"Сохранено письмо: {filepath}")
    else:
        print(f"Ошибка при получении письма с ID {email_id}")


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
    print(f"Сохранен текст письма в файл: {output_path}")


def process_emails_in_directory(directory, output_directory):
    """Проходит по всем файлам в директории, извлекает текст и сохраняет его в файл."""
    # Создаем директорию для сохранения текстов, если она не существует
    os.makedirs(output_directory, exist_ok=True)

    for filename in os.listdir(directory):
        if filename.endswith(".eml"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                email_content = f.read()

            # Извлекаем чистый текст из письма
            clean_text = extract_clean_text_from_email(email_content)

            # Формируем путь для сохранения текста
            output_filename = f"{os.path.splitext(filename)[0]}.txt"
            output_path = os.path.join(output_directory, output_filename)

            # Сохраняем чистый текст в файл
            save_clean_text_to_file(clean_text, output_path)


def main():
    load_env_variables()

    IMAP_SERVER = "outlook.office365.com"
    EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    SAVE_DIR = os.getenv("SAVE_DIR", "emails")
    OUTPUT_DIR = "extracted_texts"  # Директория для сохранения текстов

    create_directory(SAVE_DIR)
    create_directory(OUTPUT_DIR)

    mail = connect_to_mail_server(IMAP_SERVER, EMAIL_ACCOUNT, EMAIL_PASSWORD)

    sender_email = "noreply@manyvids.com"
    email_ids = fetch_emails(mail, sender_email)

    if email_ids:
        for email_id in email_ids:
            save_email(mail, email_id, SAVE_DIR)
    else:
        print(f"Нет писем от {sender_email} за последние 3 дня")

    mail.logout()

    process_emails_in_directory(SAVE_DIR, OUTPUT_DIR)


if __name__ == "__main__":
    main()
