import re
import socket
from configuration.logger_setup import logger


def domain_exists(domain):
    """Проверка существования домена через DNS-запрос"""
    try:
        logger.info(f"Проверка домена: {domain}")
        socket.gethostbyname(domain)
        logger.info(f"Домен {domain} существует")
        return True
    except socket.gaierror:
        logger.error(f"Домен {domain} не существует или недоступен")
        return False
    except UnicodeError as e:
        logger.error(f"Ошибка кодировки для домена {domain}: {e}")
        return False


def validate_emails_from_file(input_filename, output_filename):
    # Регулярное выражение для проверки email
    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    valid_emails = []
    invalid_emails = []

    # Открываем файл и читаем строки
    with open(input_filename, "r") as file:
        for line in file:
            email = line.strip()  # Убираем пробелы и символы новой строки
            logger.info(f"Проверка email: {email}")
            if re.match(email_pattern, email):
                # Извлекаем домен из email
                try:
                    domain = email.split("@")[1]
                    # Ограничиваем длину домена (например, 255 символов)
                    if len(domain) > 255:
                        logger.error(f"Домен слишком длинный: {domain}")
                        invalid_emails.append(email)
                        continue

                    if domain_exists(domain):
                        valid_emails.append(email)
                    else:
                        invalid_emails.append(email)
                except IndexError:
                    logger.error(f"Некорректный email без домена: {email}")
                    invalid_emails.append(email)
            else:
                logger.error(f"Некорректный формат email: {email}")
                invalid_emails.append(email)

    # Записываем валидные email в файл
    with open(output_filename, "w") as valid_file:
        for email in valid_emails:
            valid_file.write(email + "\n")

    return valid_emails, invalid_emails


# Пример использования
input_filename = "email.txt"
output_filename = "valid_email.txt"
valid, invalid = validate_emails_from_file(input_filename, output_filename)

logger.info(f"Valid emails saved to {output_filename}")
logger.error(f"Invalid emails: {invalid}")
