import sqlite3

from config.logger_setup import logger
from database import get_connection
from telethon.tl.functions.channels import JoinChannelRequest


def add_groups(group_links: str):
    """
    Добавляет несколько групп в базу данных.
    :param group_links: Список ссылок на группы, разделённых запятыми.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        links = [link.strip() for link in group_links.split(",") if link.strip()]
        for link in links:
            try:
                cursor.execute("INSERT INTO groups (group_link) VALUES (?)", (link,))
                logger.info(f"Группа {link} добавлена.")
            except sqlite3.IntegrityError:
                logger.warning(f"Группа {link} уже существует.")
        conn.commit()
    except Exception as e:
        logger.error(f"Ошибка при добавлении групп: {e}")
    finally:
        conn.close()
        logger.info("Соединение с базой данных закрыто после добавления групп.")


def get_groups():
    """
    Получить список всех групп.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT group_link FROM groups WHERE subscription_status = 0")
    groups = cursor.fetchall()
    conn.close()
    return [group[0] for group in groups]


async def join_groups(client, group_links: list):
    """
    Присоединяется к указанным группам.
    """
    for link in group_links:
        try:
            await client(JoinChannelRequest(link))
            logger.info(f"Успешно присоединился к группе: {link}")
        except Exception as e:
            logger.error(f"Не удалось присоединиться к группе {link}: {e}")


def get_groups_with_subscription():
    """
    Получить группы с активным статусом подписки.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, group_link FROM groups WHERE subscription_status = 1"
        )
        groups = cursor.fetchall()
        if not groups:
            logger.info("В базе данных нет подписанных групп.")
        else:
            logger.info(f"Получено {len(groups)} подписанных групп из базы данных.")
            logger.debug(f"Список подписанных групп: {groups}")

        # Проверяем, что каждая группа имеет корректную структуру
        valid_groups = [group for group in groups if len(group) > 1 and group[1]]
        if len(valid_groups) != len(groups):
            logger.warning(
                f"Некорректные записи обнаружены в результатах: {len(groups) - len(valid_groups)} пропущено."
            )

        return valid_groups
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении подписанных групп: {e}")
        return []
    finally:
        conn.close()
        logger.info(
            "Соединение с базой данных закрыто после получения подписанных групп."
        )

