from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import generate_tickets_if_empty

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Раз в сутки проверяем и добавляем билеты, если база пуста
    scheduler.add_job(generate_tickets_if_empty, "interval", hours=24)
    scheduler.start()
