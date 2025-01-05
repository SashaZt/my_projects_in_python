from configuration.logger_setup import logger
from emval import validate_email
import dns.resolver
from concurrent.futures import ThreadPoolExecutor


def check_mx_record(domain):
    """
    Проверяет наличие MX-записей для домена.
    """
    try:
        dns.resolver.resolve(domain, "MX")
        logger.info(f"Домен {domain} имеет MX-записи")
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout) as e:
        logger.warning(f"Домен {domain} не имеет MX-записей: {e}")
        return False


def validate_and_check_email(email):
    """
    Валидирует email и проверяет наличие MX-записей у домена.
    """
    email = email.strip()  # Убираем пробелы и лишние символы
    try:
        validated_email = validate_email(email)  # Валидация через emval
        domain = validated_email.normalized.split("@")[1]  # Извлекаем домен

        if check_mx_record(domain):  # Проверяем наличие MX-записей
            logger.info(f"Валидный email: {validated_email.normalized}")
            return validated_email.normalized
        else:
            logger.error(
                f"Email {email} валиден по синтаксису, но домен не имеет MX-записей"
            )
            return None
    except Exception as e:
        logger.error(f"Невалидный email: {email} - Ошибка: {str(e)}")
        return None


def process_emails(input_filename, output_filename, num_threads):
    """
    Обрабатывает email-адреса с использованием многопоточности.
    """
    valid_emails = []

    # Открываем файл с email-адресами для чтения
    with open(input_filename, "r") as infile:
        emails = infile.readlines()

    # Используем ThreadPoolExecutor для параллельной обработки email
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Многопоточная обработка email через validate_and_check_email
        results = executor.map(validate_and_check_email, emails)

    # Собираем валидные email
    valid_emails = [email for email in results if email is not None]

    # Записываем валидные email в выходной файл
    with open(output_filename, "w") as outfile:
        for valid_email in valid_emails:
            outfile.write(valid_email + "\n")

    logger.info(f"Валидные email записаны в {output_filename}")


# Пример использования
if __name__ == "__main__":
    # Передаем на вход 
    input_filename = "email.txt"
    # Получаем на выходе
    output_filename = "valid_email.txt"
    num_threads = 10  # Количество потоков

    process_emails(input_filename, output_filename, num_threads)
