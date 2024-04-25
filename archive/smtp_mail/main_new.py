# -*- mode: python ; coding: utf-8 -*-
# отправка писем с голосовым сообщением на почту
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import re
import sys
import json
import time
import os
import glob
from datetime import datetime


def load_config():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)
    config_mail = config["mail"]

    return config_mail


def send_email(callerid, subject, message, filename_wav):
    config = load_config()
    sender_email = config["sender_email"]
    recipient_email = config["recipient_email"]
    smtp_server = config["smtp_server"]
    smtp_port = config["smtp_port"]
    smtp_username = config["smtp_username"]
    smtp_password = config["smtp_password"]

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.attach(MIMEText(message, "plain"))

    try:
        with open(filename_wav, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
    except FileNotFoundError:
        print(f"The file {filename_wav} was not found")
        return

    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition", f"attachment; filename= {os.path.basename(filename_wav)}"
    )
    msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        print(
            f"Письмо отправлено от {callerid} в {datetime.now().strftime('%d.%m.%Y_%H:%M')}"
        )
    except Exception as e:
        print("Error sending email:", str(e))
    finally:
        if server is not None:
            server.quit()


def main():
    files = glob.glob("/var/spool/asterisk/voicemail/default/800/INBOX/msg0000.txt")
    if files:
        for filename in files:
            with open(filename, "r") as file:
                text = file.read()

            match = re.search(r'callerid="(.+?)"', text)
            if match:
                callerid = match.group(1)
                subject = f"Голосовое сообщение от {callerid}"
                message = "Хорошего дня"
                filename_wav = "/var/spool/asterisk/voicemail/default/800/INBOX/msg0000.WAV"  # Обратите внимание на правильный регистр расширения
                send_email(callerid, subject, message, filename_wav)

                # Удаление обработанных файлов
                for file_to_delete in glob.glob(
                    "/var/spool/asterisk/voicemail/default/800/INBOX/msg0000.*"
                ):
                    try:
                        os.remove(file_to_delete)
                        print(f"Удален файл {file_to_delete}")
                    except OSError as e:
                        print(f"Error: {e.strerror}")
    else:
        print("Голосового сообщения нету")


if __name__ == "__main__":
    main()
