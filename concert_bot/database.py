import sqlite3

# Путь к твоей базе данных
DB_PATH = 'database.db'

def get_connection():
    # Параметр check_same_thread=False критически важен для работы с APScheduler
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                city TEXT,
                seat TEXT,
                time TEXT,
                status TEXT DEFAULT 'available'
            )
        ''')
        conn.commit()

def generate_new_day(date_str, city, seats_list, time_str):
    """Исправленная функция генерации билетов"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Тот самый запрос из твоей ошибки
            for seat in seats_list:
                cursor.execute(
                    "SELECT id FROM tickets WHERE date=? AND city=? AND seat=? AND time=? LIMIT 1",
                    (date_str, city, seat, time_str)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO tickets (date, city, seat, time) VALUES (?, ?, ?, ?)",
                        (date_str, city, seat, time_str)
                    )
            conn.commit()
    except Exception as e:
        print(f"Ошибка при работе с БД: {e}")

# Добавь сюда остальные свои функции работы с БД (get_tickets и т.д.), 
# используя шаблон 'with get_connection() as conn:'
