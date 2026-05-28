# database.py
import sqlite3
from datetime import datetime

DB_NAME = "wello_searcher.db"

def init_db():
    """Инициализация базы данных и создание таблиц"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            source TEXT DEFAULT 'none',
            searches_left INTEGER DEFAULT 0,
            last_reset_date TEXT,
            is_premium INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS catches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            caught_username TEXT,
            estimated_price INTEGER,
            catch_date TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(user_id: int, username: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username, last_reset_date) VALUES (?, ?, ?)",
        (user_id, username, datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()
    conn.close()

def set_user_source(user_id: int, source: str, initial_searches: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET source = ?, searches_left = ? WHERE user_id = ?",
        (source, initial_searches, user_id)
    )
    conn.commit()
    conn.close()

def check_and_reset_daily_limit(user_id: int):
    """Проверяет дату и обновляет лимит поисков, если наступил новый день"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT last_reset_date, is_premium, searches_left FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return
        
    last_reset, is_premium, searches_left = res
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    if last_reset != current_date:
        # Если новый день, даем 3 поиска (или больше, если премиум)
        new_searches = 3 if is_premium == 0 else 15  # Премиуму можно дать больше лимитов
        cursor.execute(
            "UPDATE users SET searches_left = ?, last_reset_date = ? WHERE user_id = ?",
            (new_searches, current_date, user_id)
        )
        conn.commit()
        
    conn.close()

def deduct_search(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET searches_left = searches_left - 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def add_catch(user_id: int, caught_username: str, price: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO catches (user_id, caught_username, estimated_price, catch_date) VALUES (?, ?, ?, ?)",
        (user_id, caught_username, price, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()

def get_user_catches(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT caught_username, estimated_price FROM catches WHERE user_id = ? ORDER BY id DESC", (user_id,))
    catches = cursor.fetchall()
    conn.close()
    return catches

def activate_premium(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
