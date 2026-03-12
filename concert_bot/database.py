import sqlite3

# Настройки городов и мест (твои данные)
cities = {
    "Москва": ["Ряд 1, Место 1", "Ряд 1, Место 2", "Ряд 2, Место 1"],
    "Питер": ["Сектор А, 1", "Сектор А, 2", "VIP 1"],
    "Казань": ["Зал 1, 10", "Зал 1, 11"]
}

times = ["18:00", "20:00", "22:00"]

DB_PATH = 'database.db'

def get_connection():
    """Создает подключение к БД, разрешая работу из разных потоков."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    """Инициализация таблиц при запуске."""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Создаем таблицу билетов, если её нет
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                city TEXT,
                seat TEXT,
                time TEXT,
                is_sold INTEGER DEFAULT 0,
                user_id INTEGER DEFAULT NULL
            )
        ''')
        conn.commit()

def generate_new_day():
    """
    Функция для планировщика (scheduler).
    Генерирует билеты на неделю вперед, если их еще нет.
    """
    from datetime import datetime, timedelta
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Генерируем даты на ближайшие 7 дней
        for i in range(7):
            date_str = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            
            for city, seats in cities.items():
                for seat in seats:
                    for t in times:
                        # Проверяем, существует ли уже такой билет
                        cursor.execute("""
                            SELECT id FROM tickets 
                            WHERE date=? AND city=? AND seat=? AND time=?
                        """, (date_str, city, seat, t))
                        
                        if not cursor.fetchone():
                            cursor.execute("""
                                INSERT INTO tickets (date, city, seat, time, is_sold)
                                VALUES (?, ?, ?, ?, 0)
                            """, (date_str, city, seat, t))
        
        conn.commit()
        print(f"[{datetime.now()}] База билетов обновлена.")

# Вызываем инициализацию при импорте файла, чтобы таблицы создались сразу
init_db()
