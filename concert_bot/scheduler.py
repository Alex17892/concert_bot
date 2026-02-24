from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import generate_new_day

scheduler = AsyncIOScheduler()

def start_scheduler():
    # Запуск генерации билетов каждый день в 00:00
    scheduler.add_job(generate_new_day, "cron", hour=0, minute=0)
    scheduler.start()