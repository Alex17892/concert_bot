import sqlite3
import os
from datetime import datetime, timedelta

# Подключение к базе (используем то же имя, что в bot.py)
DB_PATH = "tickets.db"
conn = sqlite3.connect(DB_PATH)
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

# Функция генерации билетов
def generate_tickets_if_empty():
    cursor.execute("SELECT COUNT(*) FROM tickets")
    if cursor.fetchone()[0] == 0:
        print("База пуста. Генерирую билеты...")
        today = datetime.now()

        for day_offset in range(7):
            concert_date = (today + timedelta(days=day_offset)).strftime("%Y-%m-%d")

            for city, seats in cities.items():
                for seat in seats:
                    for t in times:
                        # Создаём по 5 билетов на каждую комбинацию (30 — это очень много, база будет весить гигабайты)
                        for _ in range(5): 
                            cursor.execute("""
                                INSERT INTO tickets (date, city, seat, time, is_sold)
                                VALUES (?, ?, ?, ?, 0)
                            """, (concert_date, city, seat, t))
        conn.commit()
        print("Билеты успешно созданы!")

# ЗАПУСКАЕМ ГЕНЕРАЦИЮ ПРИ ЗАГРУЗКЕ ФАЙЛА
generate_tickets_if_empty()
