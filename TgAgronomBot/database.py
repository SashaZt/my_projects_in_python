import sqlite3

class Database:
    def __init__(self, db_file):
        self.db_file = db_file

    def create_connection(self):
        return sqlite3.connect(self.db_file, check_same_thread=False)

    def initialize_db(self):
        connection = self.create_connection()
        with connection:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    nickname TEXT,
                    signup TIMESTAMP,
                    trial_duration INTEGER DEFAULT 172800  -- 2 дня в секундах
                )
            """)

    def add_user(self, user_id, nickname, signup_time):
        connection = self.create_connection()
        with connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (user_id, nickname, signup) VALUES (?, ?, ?)", (user_id, nickname, signup_time))

    def user_exists(self, user_id):
        connection = self.create_connection()
        with connection:
            cursor = connection.cursor()
            result = cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchall()
            return bool(len(result))

    def get_signup_time(self, user_id):
        connection = self.create_connection()
        with connection:
            cursor = connection.cursor()
            result = cursor.execute("SELECT signup FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return result[0] if result else None

    def get_trial_duration(self, user_id):
        connection = self.create_connection()
        with connection:
            cursor = connection.cursor()
            result = cursor.execute("SELECT trial_duration FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return result[0] if result else 172800  # Возвращаем 2 дня (по умолчанию)

    def set_trial_duration(self, user_id, duration):
        connection = self.create_connection()
        with connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET trial_duration = ? WHERE user_id = ?", (duration, user_id))

    def set_nickname(self, user_id, nickname):
        connection = self.create_connection()
        with connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET nickname = ? WHERE user_id = ?", (nickname, user_id))

