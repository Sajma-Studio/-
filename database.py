import sqlite3

class Database:
    def __init__(self, db_file):
        # Використовуємо SQLite для модератора (простіше для зберігання на Render)
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        with self.conn:
            # Таблиця для статистики повідомлень та варнів
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    name TEXT,
                    messages INTEGER DEFAULT 0,
                    warns INTEGER DEFAULT 0
                )
            """)
            # Таблиця для фільтрів чату
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    chat_id BIGINT PRIMARY KEY,
                    anti_rus INTEGER DEFAULT 0,
                    anti_mat INTEGER DEFAULT 0
                )
            """)

    def update_stats(self, uid, name):
        """Оновлює кількість повідомлень користувача"""
        with self.conn:
            self.cursor.execute("""
                INSERT INTO users (id, name, messages) VALUES (?, ?, 1)
                ON CONFLICT(id) DO UPDATE SET 
                messages = users.messages + 1, name = ?
            """, (uid, name, name))

    def add_warn(self, uid):
        """Додає варн і повертає поточну кількість"""
        with self.conn:
            self.cursor.execute("UPDATE users SET warns = warns + 1 WHERE id = ?", (uid,))
            self.cursor.execute("SELECT warns FROM users WHERE id = ?", (uid,))
            res = self.cursor.fetchone()
            return res[0] if res else 1

    def reset_warns(self, uid):
        """Скидає варни (після бану)"""
        with self.conn:
            self.cursor.execute("UPDATE users SET warns = 0 WHERE id = ?", (uid,))

    def get_user(self, uid):
        """Отримує дані для команди 'стат'"""
        self.cursor.execute("SELECT messages, warns FROM users WHERE id = ?", (uid,))
        return self.cursor.fetchone()

    def get_setting(self, chat_id, key):
        """Перевіряє, чи ввімкнено Анти-Рос або Анти-Мат"""
        self.cursor.execute(f"SELECT {key} FROM settings WHERE chat_id = ?", (chat_id,))
        res = self.cursor.fetchone()
        return res[0] if res else 0

    def set_setting(self, chat_id, key, val):
        """Вмикає/вимикає фільтри"""
        with self.conn:
            self.cursor.execute(f"""
                INSERT INTO settings (chat_id, {key}) VALUES (?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET {key} = ?
            """, (chat_id, val, val))
