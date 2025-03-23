import asyncio
import datetime
import json
import sqlite3
import sys
import time
from pathlib import Path

import gspread
import nodriver as uc
import schedule
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials
from loguru import logger

# Настройка директорий и логирования
# Настройка путей
current_directory = Path.cwd()
config_directory = current_directory / "config"
html_directory = current_directory / "html"
data_directory = current_directory / "data"
log_directory = current_directory / "log"

data_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)
output_json_file = data_directory / "output.json"
config_file = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"
log_file_path = log_directory / "log_message.log"
output_xlsx_file = data_directory / "output.xlsx"
db_path = data_directory / "tikleap_users.db"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)


# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def get_config():
    """Загружает конфигурацию из JSON файла."""
    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


# Загрузка конфигурации
config = get_config()
SPREADSHEET = config["google"]["spreadsheet"]
SHEET = config["google"]["sheet"]


def get_google_sheet():
    """Подключается к Google Sheets и возвращает указанный лист."""
    try:
        # Новый способ аутентификации с google-auth
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )

        # Авторизация в gspread с новыми учетными данными
        client = gspread.authorize(credentials)

        # Открываем таблицу по ключу и возвращаем лист
        spreadsheet = client.open_by_key(SPREADSHEET)
        logger.info("Успешное подключение к Google Spreadsheet.")
        return spreadsheet.worksheet(SHEET)
    except FileNotFoundError:
        logger.error("Файл учетных данных не найден. Проверьте путь.")
        raise FileNotFoundError("Файл учетных данных не найден. Проверьте путь.")
    except gspread.exceptions.APIError as e:
        logger.error(f"Ошибка API Google Sheets: {e}")
        raise
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        raise


# Получение листа Google Sheets
sheet = get_google_sheet()


def ensure_row_limit(sheet, required_rows=10000):
    """Увеличивает количество строк в листе Google Sheets, если их меньше требуемого количества."""
    current_rows = len(sheet.get_all_values())
    if current_rows < required_rows:
        sheet.add_rows(required_rows - current_rows)


ensure_row_limit(sheet, 1000)


async def process_country(browser, country_code):
    try:
        logger.info(f"Обработка страны: {country_code}")

        # Переходим на страницу страны
        target_page = await browser.get(
            f"https://www.tikleap.com/country/{country_code}"
        )
        await asyncio.sleep(2)
        await target_page  # Обновляем страницу

        # Проверяем, успешно ли перешли
        logger.info(f"Текущий URL: {target_page.url}")

        if f"country/{country_code}" in target_page.url:
            logger.info(f"Успешно перешли на страницу страны {country_code}")

            # Прокручиваем вниз и ищем кнопку View More
            max_attempts = 5  # Максимальное количество попыток нажатия
            attempts_without_button = 0

            for attempt in range(max_attempts):
                # Прокрутка страницы вниз
                logger.info(
                    f"Прокручиваем страницу вниз (попытка {attempt+1}/{max_attempts})..."
                )
                await target_page.scroll_down(500)  # Прокрутка на 500 пикселей
                await asyncio.sleep(1)  # Даем время для загрузки

                # Ищем кнопку View More
                view_more_button = await target_page.select(".ranklist-table-more")

                # Если кнопка найдена, нажимаем на нее
                if view_more_button:
                    logger.info("Найдена кнопка 'View More'. Нажимаем...")
                    try:
                        await view_more_button.click()
                        logger.info("Нажали на кнопку 'View More'")
                    except Exception as e:
                        logger.error(f"Ошибка при нажатии на 'View More': {e}")
                        try:
                            await view_more_button.mouse_click()
                            logger.info("Нажали на 'View More' через mouse_click()")
                        except Exception as e:
                            logger.error(f"Ошибка при нажатии через mouse_click(): {e}")

                    await asyncio.sleep(1)  # Ждем загрузки новых данных
                    attempts_without_button = 0
                else:
                    attempts_without_button += 1
                    logger.warning(
                        f"Кнопка 'View More' не найдена (попытка {attempts_without_button}/3)"
                    )

                    # Если кнопка не найдена 3 раза подряд, считаем что загрузили все данные
                    if attempts_without_button >= 3:
                        logger.info(
                            "Кнопка 'View More' не найдена 3 раза подряд. Загрузка завершена."
                        )
                        break

            # Сохраняем страницу
            file_path = html_directory / f"country_{country_code}.html"
            logger.info(f"Сохраняем страницу как {file_path}")

            # Получаем HTML-контент страницы
            html_content = await target_page.get_content()

            # Создаем файл и сохраняем в него HTML
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(html_content)

            logger.success(f"Страница успешно сохранена: {file_path}")
            return True
        else:
            logger.error(f"Не удалось перейти на страницу страны {country_code}")
            return False

    except Exception as e:
        logger.error(f"Ошибка при обработке страны {country_code}: {str(e)}")
        return False


async def main():
    # Загружаем список стран из JSON-файла
    try:

        country_list = config.get("country", [])

        if not country_list:
            logger.error("Список стран пуст или не найден в файле country.json")
            return

        logger.info(f"Загружено {len(country_list)} стран: {', '.join(country_list)}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке списка стран: {str(e)}")
        return

    browser = None
    try:
        # Инициализируем браузер
        browser = await uc.start(headless=False)

        # Сначала выполняем вход
        logger.info("Переходим на страницу логина...")
        login_page = await browser.get("https://www.tikleap.com/login")
        await asyncio.sleep(2)

        # Проверяем на блокировку Cloudflare
        content = await login_page.get_content()
        if (
            "Please enable cookies" in content
            or "Sorry, you have been blocked" in content
        ):
            logger.error("Обнаружена блокировка Cloudflare. Обновляем...")
            await login_page.reload()
            await asyncio.sleep(2)

        # Вводим email
        logger.info("Вводим email...")
        email_field = await login_page.select("input#email")
        if email_field:
            await email_field.send_keys("37200@starlivemail.com")
            await asyncio.sleep(0.5)
        else:
            logger.error("Поле email не найдено!")
            return

        # Вводим пароль
        logger.info("Вводим пароль...")
        password_field = await login_page.select("input#password")
        if password_field:
            await password_field.send_keys("bfnsa232@1!dsA")
            await asyncio.sleep(0.5)
        else:
            logger.error("Поле пароля не найдено!")
            return

        # Ищем кнопку логина
        logger.info("Ищем кнопку логина...")
        login_button = await login_page.select(".form-action button")

        if not login_button:
            login_button = await login_page.find("Log In", best_match=True)
            logger.info("Использую поиск по тексту для кнопки")

        if not login_button:
            login_button = await login_page.select("form button")
            logger.info("Использую поиск кнопки на форме")

        if login_button:
            logger.info("Кнопка логина найдена. Нажимаем...")
            await asyncio.sleep(1)

            try:
                await login_button.click()
                logger.info("Нажали на кнопку входа через .click()")
            except Exception as e:
                logger.error(f"Ошибка при нажатии кнопки через click(): {e}")
                try:
                    await login_button.mouse_click()
                    logger.info("Нажали на кнопку входа через .mouse_click()")
                except Exception as e:
                    logger.error(f"Ошибка при нажатии кнопки через mouse_click(): {e}")

            logger.info("Ждем обработки входа...")
            await asyncio.sleep(5)

            # Проверяем, успешно ли выполнили вход
            await login_page
            await login_page.reload()

            current_url = login_page.url
            logger.info(f"Текущий URL после попытки входа: {current_url}")

            if "login" in current_url:
                logger.warning("Все еще на странице логина. Вход мог не сработать.")

                # Проверяем наличие сообщений об ошибке
                error_message = await login_page.select(".form-error")
                if error_message:
                    error_text = await error_message.get_property("textContent")
                    logger.warning(f"Сообщение об ошибке: {error_text}")

                # Пытаемся сделать вход вручную
                logger.info("Даем возможность для ручного входа (30 секунд)...")
                await asyncio.sleep(30)

            # Обрабатываем каждую страну из списка
            successful_countries = 0
            for country in country_list:
                success = await process_country(browser, country)
                if success:
                    successful_countries += 1
                # Делаем небольшую паузу между странами
                await asyncio.sleep(2)

            logger.info(
                f"Обработка завершена. Успешно обработано {successful_countries} из {len(country_list)} стран."
            )

        else:
            logger.error("Кнопка логина не найдена!")

    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")

    finally:
        # Закрываем браузер
        if browser:
            try:
                await browser.stop()
                logger.info("Браузер закрыт")
            except Exception as e:
                logger.error(f"Ошибка при закрытии браузера: {str(e)}")


# Функция для обработки всех имеющихся HTML-файлов
def process_all_html_files():
    try:
        logger.info("Начинаем обработку всех HTML-файлов...")

        # Получаем список всех HTML-файлов в директории
        html_files = list(html_directory.glob("country_*.html"))

        if not html_files:
            logger.warning("HTML-файлы не найдены в директории html/")
            return

        logger.info(f"Найдено {len(html_files)} HTML-файлов для обработки")

        # Для сохранения всех пользователей в один файл
        all_users_data = []

        # Обрабатываем каждый файл
        processed_files = 0
        for file_path in html_files:
            country_code = file_path.stem.replace("country_", "")
            logger.info(
                f"Обработка файла {file_path.name} для страны {country_code}..."
            )

            # Парсим данные из HTML-файла
            users_data = parse_html_file(file_path)

            # Сохраняем извлеченные данные
            if users_data:
                save_user_data(users_data, country_code)
                all_users_data.extend(users_data)
                processed_files += 1

        # Сохраняем все данные в один общий файл
        with open(output_json_file, "w", encoding="utf-8") as f:
            json.dump(all_users_data, f, ensure_ascii=False, indent=4)
        logger.success(f"Все данные успешно сохранены в общий файл: {output_json_file}")

        logger.success(
            f"Обработка завершена. Успешно обработано {processed_files} из {len(html_files)} файлов."
        )

        save_users_to_sqlite(all_users_data, db_path)

        # Экспортируем данные в Google Sheets
        export_unloaded_users_to_google_sheets()

    except Exception as e:
        logger.error(f"Ошибка при обработке HTML-файлов: {str(e)}")
        logger.exception("Подробная информация об ошибке:")


def save_user_data(users_data, country_code):
    """
    Функция для сохранения данных о пользователях в JSON файл
    """
    try:
        file_path = data_directory / f"users_{country_code}.json"

        # Проверяем существует ли файл и загружаем данные из него
        existing_data = []
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(
                        f"Не удалось прочитать существующие данные из {file_path}. Создаем новый файл."
                    )

        # Добавляем новые данные
        combined_data = existing_data + users_data

        # Сохраняем объединенные данные
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=4)

        logger.success(f"Данные успешно сохранены в {file_path}")

    except Exception as e:
        logger.error(f"Ошибка при сохранении данных: {e}")


def parse_html_file(file_path):
    """
    Функция для парсинга HTML-файла и извлечения данных о пользователях
    """
    try:
        # Получаем код страны из имени файла (например, country_kz.html -> kz)
        country_code = Path(file_path).stem.replace("country_", "")

        # Получаем текущую дату и время в нужном формате
        current_datetime = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        # Открываем и читаем HTML-файл
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(content, "lxml")

        # Находим все строки в таблице рейтинга
        table_rows = soup.select(".ranklist-table-row")

        users_data = []

        for row in table_rows:
            try:
                # Извлекаем нужные данные
                profile_link = row.get("href", "")

                # Проверяем, что ссылка существует и не пуста
                if not profile_link:
                    logger.warning(f"Пропуск строки - отсутствует ссылка на профиль")
                    continue

                # Находим место в рейтинге с проверкой
                rank_element = row.select_one(".ranklist-place-wrapper span")
                if not rank_element:
                    logger.warning(
                        f"Пропуск профиля {profile_link} - отсутствует элемент ранга"
                    )
                    continue
                rank = rank_element.text.strip()

                # Находим заработок с проверкой
                earning_element = row.select_one(".ranklist-earning-wrapper span.price")
                if not earning_element:
                    logger.warning(
                        f"Пропуск профиля {profile_link} - отсутствует элемент заработка"
                    )
                    continue
                earning = earning_element.text.strip()

                # Создаем объект с данными пользователя
                user_data = {
                    "current_datetime": current_datetime,
                    "country_code": country_code,
                    "profile_link": profile_link,
                    "rank": rank,
                    "earning": earning,
                }

                users_data.append(user_data)

            except Exception as e:
                logger.error(f"Ошибка при обработке строки таблицы: {e}")

        logger.success(
            f"Успешно обработан файл {file_path}. Извлечено {len(users_data)} пользователей."
        )

        return users_data

    except Exception as e:
        logger.error(f"Ошибка при парсинге файла {file_path}: {e}")
        return []


def save_users_to_sqlite(users_data, db_path=None):
    """
    Функция для сохранения данных о пользователях в SQLite базу данных

    Args:
        users_data (list): Список словарей с данными пользователей
        db_path (str or Path, optional): Путь к файлу базы данных
    """
    try:
        if not users_data:
            logger.warning("Нет данных для сохранения в базу данных")
            return

        # Устанавливаем путь к базе данных по умолчанию, если не указан
        if db_path is None:
            db_path = data_directory / "tikleap_users.db"

        logger.info(f"Сохранение данных в базу данных: {db_path}")

        # Подключаемся к БД
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Создаем таблицу, если она не существует
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS tikleap_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            current_datetime TEXT,
            country_code TEXT,
            profile_link TEXT UNIQUE,
            rank INTEGER,
            earning TEXT,
            loading_table BOOLEAN DEFAULT 0
        )
        """
        )

        # Добавляем или обновляем данные пользователей
        added_count = 0
        updated_count = 0

        for user in users_data:
            try:
                # Проверяем валидность данных
                if not user.get("profile_link"):
                    logger.warning("Пропуск записи: отсутствует profile_link")
                    continue

                # Преобразуем rank в int с обработкой ошибок
                try:
                    rank = int(user.get("rank", 0))
                except (ValueError, TypeError):
                    logger.warning(
                        f"Неверный формат rank для {user.get('profile_link')}, устанавливаем 0"
                    )
                    rank = 0

                # Проверяем, существует ли уже такой пользователь
                cursor.execute(
                    "SELECT * FROM tikleap_users WHERE profile_link = ?",
                    (user["profile_link"],),
                )
                existing_user = cursor.fetchone()

                if existing_user:
                    # Обновляем информацию о пользователе
                    cursor.execute(
                        """
                    UPDATE tikleap_users SET 
                        current_datetime = ?,
                        country_code = ?,
                        rank = ?,
                        earning = ?
                    WHERE profile_link = ?
                    """,
                        (
                            user["current_datetime"],
                            user["country_code"],
                            rank,
                            user["earning"],
                            user["profile_link"],
                        ),
                    )
                    updated_count += 1
                else:
                    # Добавляем нового пользователя
                    cursor.execute(
                        """
                    INSERT INTO tikleap_users 
                    (current_datetime, country_code, profile_link, rank, earning, loading_table) 
                    VALUES (?, ?, ?, ?, ?, 0)
                    """,
                        (
                            user["current_datetime"],
                            user["country_code"],
                            user["profile_link"],
                            rank,
                            user["earning"],
                        ),
                    )
                    added_count += 1
            except Exception as e:
                logger.error(
                    f"Ошибка при обработке пользователя {user.get('profile_link', 'Unknown')}: {e}"
                )

        # Сохраняем изменения
        conn.commit()

        # Выводим статистику
        logger.success(
            f"Данные успешно сохранены в БД: добавлено {added_count}, обновлено {updated_count} записей"
        )

        # Получаем общее количество записей в базе
        cursor.execute("SELECT COUNT(*) FROM tikleap_users")
        total_count = cursor.fetchone()[0]
        logger.info(f"Всего записей в базе данных: {total_count}")

        # Получаем количество записей, готовых к выгрузке
        cursor.execute("SELECT COUNT(*) FROM tikleap_users WHERE loading_table = 0")
        unloaded_count = cursor.fetchone()[0]
        logger.info(f"Ожидают выгрузки в Google Sheets: {unloaded_count} записей")

        # Закрываем соединение с БД
        conn.close()

    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в базу данных: {e}")
        logger.exception("Подробная информация об ошибке:")


def export_unloaded_users_to_google_sheets():
    """
    Функция для выгрузки пользователей, у которых loading_table = False, в Google Sheets
    """
    try:
        logger.info("Выгрузка данных в Google Sheets...")
        if not db_path.exists():
            logger.error(f"База данных не найдена по пути: {db_path}")
            return

        # Подключаемся к БД
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Получаем все записи с loading_table = False
        cursor.execute(
            """
        SELECT current_datetime, country_code, profile_link, rank, earning
        FROM tikleap_users
        WHERE loading_table = 0
        ORDER BY country_code, rank
        """
        )

        unloaded_users = cursor.fetchall()

        if not unloaded_users:
            logger.info("Нет новых записей для выгрузки в Google Sheets")
            conn.close()
            return

        logger.info(
            f"Найдено {len(unloaded_users)} записей для выгрузки в Google Sheets"
        )

        # Получаем лист Google Sheets
        sheet = get_google_sheet()

        # Проверяем, есть ли заголовки
        headers = sheet.row_values(1)
        expected_headers = [
            "Дата добавления",
            "Источник",
            "Ссылка",
            "Место в рейтинге",
            "Заработок",
        ]

        # Если нет заголовков или они не соответствуют ожидаемым, добавляем их
        if not headers or headers != expected_headers:
            sheet.clear()  # Очищаем лист для установки заголовков
            sheet.update(values=[expected_headers], range_name="A1:E1")
            logger.info("Добавлены заголовки в Google Sheets")

        # Находим первую пустую строку
        existing_data = sheet.get_all_values()
        next_row = len(existing_data) + 1

        # Подготавливаем данные для записи
        rows_to_insert = []
        updated_user_ids = []

        for user in unloaded_users:
            rows_to_insert.append(list(user))

            # Получаем ID пользователя для последующего обновления loading_table
            cursor.execute(
                """
            SELECT id FROM tikleap_users 
            WHERE profile_link = ?
            """,
                (user[2],),
            )

            user_id = cursor.fetchone()
            if user_id:
                updated_user_ids.append(user_id[0])

        # Записываем данные в Google Sheets
        if rows_to_insert:
            # Определяем диапазон для записи (A{next_row}:E{next_row+len(rows_to_insert)-1})
            range_to_update = f"A{next_row}:E{next_row+len(rows_to_insert)-1}"

            # Исправлено: сначала values, потом range_name
            sheet.update(values=rows_to_insert, range_name=range_to_update)

            logger.success(
                f"Успешно выгружено {len(rows_to_insert)} записей в Google Sheets"
            )

            # Обновляем флаг loading_table для выгруженных записей
            for user_id in updated_user_ids:
                cursor.execute(
                    """
                UPDATE tikleap_users
                SET loading_table = 1
                WHERE id = ?
                """,
                    (user_id,),
                )

            conn.commit()
            logger.info(
                f"Обновлен статус loading_table для {len(updated_user_ids)} записей"
            )

        # Закрываем соединение с БД
        conn.close()

    except Exception as e:
        logger.error(f"Ошибка при выгрузке данных в Google Sheets: {e}")
        logger.exception("Подробная информация об ошибке:")
        # Если возникла ошибка, пытаемся закрыть соединение с БД
        try:
            if "conn" in locals() and conn:
                conn.close()
        except:
            pass


if __name__ == "__main__":

    def job():
        logger.info("Запуск плановой задачи...")
        try:
            uc.loop().run_until_complete(main())
            process_all_html_files()
            export_unloaded_users_to_google_sheets()
            logger.success("Плановая задача успешно выполнена.")
        except Exception as e:
            logger.error(f"Ошибка при выполнении плановой задачи: {e}")

    # Запускаем задачу сразу при старте программы
    job()

    # Планируем выполнение задачи каждые 5 минут
    schedule.every(5).minutes.do(job)

    logger.info("Планировщик запущен. Задача будет выполняться каждые 5 минут.")

    # Бесконечный цикл для выполнения запланированных задач
    while True:
        schedule.run_pending()
        time.sleep(1)
