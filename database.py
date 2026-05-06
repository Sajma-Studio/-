import sqlite3

class Database:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Таблиця для юзерів (статистика + варни)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                full_name TEXT,
                messages_count INTEGER DEFAULT 0,
                warns INTEGER DEFAULT 0
            )
        """)
        # Таблиця для налаштувань кожного чату
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id BIGINT PRIMARY KEY,
                anti_rus INTEGER DEFAULT 0,
                anti_mat INTEGER DEFAULT 0,
                anti_flood INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def update_user(self, user_id, name):
        self.cursor.execute("""
            INSERT INTO users (user_id, full_name, messages_count) 
            VALUES (?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET 
            messages_count = messages_count + 1, full_name = ?
        """, (user_id, name, name))
        self.conn.commit()

    def add_warn(self, user_id):
        self.cursor.execute("UPDATE users SET warns = warns + 1 WHERE user_id = ?", (user_id,))
        self.cursor.execute("SELECT warns FROM users WHERE user_id = ?", (user_id,))
        res = self.cursor.fetchone()
        self.conn.commit()
        return res[0] if res else 0

    def reset_warns(self, user_id):
        self.cursor.execute("UPDATE users SET warns = 0 WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def get_setting(self, chat_id, setting):
        self.cursor.execute(f"SELECT {setting} FROM chat_settings WHERE chat_id = ?", (chat_id,))
        res = self.cursor.fetchone()
        return res[0] if res else 0

    def toggle_setting(self, chat_id, setting, value):
        self.cursor.execute(f"""
            INSERT INTO chat_settings (chat_id, {setting}) VALUES (?, ?) 
            ON CONFLICT(chat_id) DO UPDATE SET {setting} = ?
        """, (chat_id, value, value))
        self.conn.commit()
