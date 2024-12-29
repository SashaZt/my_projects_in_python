from database import get_connection
from config.logger_setup import logger

def add_message(message_text):
    """
    Добавляет сообщение в базу данных.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO messages (message_text) VALUES (?)", (message_text,))
        conn.commit()
        logger.info(f"Сообщение добавлено в базу данных: '{message_text}'")
    except Exception as e:
        logger.error(f"Ошибка при добавлении сообщения: {e}")
    finally:
        conn.close()
        logger.info("Соединение с базой данных закрыто после добавления сообщения.")

def get_messages():
    """
    Получить все сообщения из базы данных.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Извлекаем все сообщения, упорядоченные по времени создания
        cursor.execute("SELECT id, message_text FROM messages ORDER BY created_at DESC")
        messages = cursor.fetchall()
        logger.info(f"Получено {len(messages)} сообщений из базы данных.")
        return messages
    except Exception as e:
        logger.error(f"Ошибка при получении сообщений: {e}")
        return []
    finally:
        conn.close()
        logger.info("Соединение с базой данных закрыто после получения сообщений.")
