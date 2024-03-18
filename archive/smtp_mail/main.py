import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import re
import os
import glob
from datetime import datetime



def main():
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d.%m.%Y_%H:%M")
    while True:  # бесконечный цикл
        files = glob.glob('/var/spool/asterisk/voicemail/default/800/INBOX/msg0000.txt')  # получаем список файлов с маской 'msg0000.txt'
        if files:
            print(f"Новый файл появился в {formatted_time}")
            for filename in files:  # для каждого найденного файла
                with open(filename, 'r') as file:
                    text = file.read()

                match = re.search(r'callerid="(.+?)"', text)
                callerid = ''
                if match:
                    callerid = match.group(1)
                sender_email = "iceteam0800@gmail.com"  # отправитель
                recipient_email = "iceteam.zt@ukr.net"  # Получатель

                subject = f'Голосовое сообщение от {callerid}'  # Тема письма
                message = "Хорошего дня"  # Текст письма

                # SMTP server configuration (example: Gmail)

                smtp_server = "smtp.gmail.com"
                smtp_port = 587
                smtp_username = "iceteam0800@gmail.com"
                smtp_password = "fccyjaoypsznqfkg"  # Пароли приложений

                msg = MIMEMultipart()
                msg["Subject"] = subject
                msg["From"] = sender_email
                msg["To"] = recipient_email

                # Attach the text part
                msg.attach(MIMEText(message, 'plain'))

                filename_wav = "/var/spool/asterisk/voicemail/default/800/INBOX/msg0000.wav"  # Вложение
                try:
                    with open(filename_wav, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                except FileNotFoundError:
                    print(f"The file {filename_wav} was not found")
                    continue  # переходим к следующему файлу

                encoders.encode_base64(part)

                # Add header as pdf attachment
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {filename_wav}",
                )

                msg.attach(part)

                server = None
                try:
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.sendmail(sender_email, recipient_email, msg.as_string())
                    print(f"Письмо отправлено в {formatted_time}")
                    files = glob.glob('/var/spool/asterisk/voicemail/default/800/INBOX/msg0000*')
                    for file in files:
                        try:
                            os.remove(file)
                        except OSError as e:
                            print(f"Error: {file} : {e.strerror}")
                except Exception as e:
                    print("Error sending email:", str(e))
                finally:
                    if server is not None:
                        server.quit()
        else:
            continue

        time.sleep(30)  # ждем минуту перед следующей проверкой
def scrap():
    pass




if __name__ == '__main__':
    main()
    # scrap()

