import sqlite3
from datetime import datetime, timedelta

# Подключение к базе
conn = sqlite3.connect("tickets.db")
cursor = conn.cursor()

# Города и места
cities = {
    "Москва": ["Лежачее", "Сидячее", "Стоячее"],
    "Тула": ["Сидячее", "Лежачее", "Стоячее"],
    "Солнечногорск": ["Стоячее"]
}

# Время концертов
times = [f"{h}:00" for h in range(10, 21)]

# Создание таблицы
cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    city TEXT,
    seat TEXT,
    time TEXT,
    is_sold INTEGER DEFAULT 0,
    user_id INTEGER
)
""")
conn.commit()

# Генерация билетов на 7 дней вперёд
def generate_new_day():
    today = datetime.now()
    for day_offset in range(7):
        concert_date = (today + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        for city, seats in cities.items():
            for seat in seats:
                for t in times:
                    # Проверяем, есть ли уже билеты на эту дату и город, чтобы не дублировать
                    cursor.execute("SELECT id FROM tickets WHERE date=? AND city=? AND seat=? AND time=? LIMIT 1", 
                                 (concert_date, city, seat, t))
                    if not cursor.fetchone():
                        # создаём по 5 билетов на каждую комбинацию (30 может быть много для теста)
                        for _ in range(5):
                            cursor.execute("""
                                INSERT INTO tickets (date, city, seat, time, is_sold)
                                VALUES (?, ?, ?, ?, 0)
                            """, (concert_date, city, seat, t))
    conn.commit()

# --- ВАЖНОЕ ДОПОЛНЕНИЕ ---
# Запускаем генерацию сразу при запуске бота, если база пуста
cursor.execute("SELECT COUNT(*) FROM tickets")
if cursor.fetchone()[0] == 0:
    print("База пуста, генерирую билеты...")
    generate_new_day()
