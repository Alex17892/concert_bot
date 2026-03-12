import asyncio
import qrcode
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile
)
from aiogram.filters import CommandStart
from config import BOT_TOKEN
from database import cursor, conn, cities, times
from scheduler import start_scheduler
from keyboards.main_kb import main_kb

# Создаем папку для QR-кодов заранее
QR_DIR = "static/qr"
if not os.path.exists(QR_DIR):
    os.makedirs(QR_DIR)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_state = {}

# Кнопки выбора даты
def calendar_keyboard():
    from datetime import datetime, timedelta
    kb = []
    for i in range(7):
        day = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        kb.append([
            InlineKeyboardButton(text=day, callback_data=f"date_{day}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Добро пожаловать 🎶", reply_markup=main_kb)


@dp.message(F.text == "Выбрать день")
async def choose_day(message: Message):
    await message.answer("Выберите день:", reply_markup=calendar_keyboard())


@dp.callback_query(F.data.startswith("date_"))
async def choose_city(callback: CallbackQuery):
    date = callback.data.split("_")[1]
    user_state[callback.from_user.id] = {"date": date}

    kb = [[InlineKeyboardButton(text=city, callback_data=f"city_{city}")]
          for city in cities.keys()]

    await callback.message.edit_text(
        "Выберите город:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


@dp.callback_query(F.data.startswith("city_"))
async def choose_seat(callback: CallbackQuery):
    city = callback.data.split("_")[1]
    user_state[callback.from_user.id]["city"] = city

    seats = cities[city]
    kb = [[InlineKeyboardButton(text=seat, callback_data=f"seat_{seat}")]
          for seat in seats]

    await callback.message.edit_text(
        "Выберите место:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


@dp.callback_query(F.data.startswith("seat_"))
async def choose_time(callback: CallbackQuery):
    seat = callback.data.split("_")[1]
    user_state[callback.from_user.id]["seat"] = seat

    kb = [[InlineKeyboardButton(text=t, callback_data=f"time_{t}")]
          for t in times]

    await callback.message.edit_text(
        "Выберите время:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


@dp.callback_query(F.data.startswith("time_"))
async def buy_ticket(callback: CallbackQuery):
    time = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    if user_id not in user_state:
        await callback.message.answer("Ошибка данных. Начните заново с /start")
        return
        
    data = user_state[user_id]
    data["time"] = time

    cursor.execute("""
        SELECT id FROM tickets
        WHERE date=? AND city=? AND seat=? AND time=? AND is_sold=0
        LIMIT 1
    """, (data["date"], data["city"], data["seat"], time))

    ticket = cursor.fetchone()

    if not ticket:
        await callback.message.answer("Билет уже продан ❌")
        return

    ticket_id = ticket[0]

    cursor.execute(
        "UPDATE tickets SET is_sold=1, user_id=? WHERE id=?",
        (user_id, ticket_id)
    )
    conn.commit()

    # Текст внутри QR-кода
    qr_text = (
        f"Билет №{ticket_id}\n"
        f"Дата: {data['date']}\n"
        f"Город: {data['city']}\n"
        f"Место: {data['seat']}\n"
        f"Время: {data['time']}"
    )

    # Генерация QR с сохранением в спец. папку
    file_path = os.path.join(QR_DIR, f"ticket_{ticket_id}.png")
    img = qrcode.make(qr_text)
    img.save(file_path)

    # Отправка фото
    photo = FSInputFile(file_path)

    await callback.message.answer_photo(
        photo=photo,
        caption=(
            f"🎟 Ваш билет\n\n"
            f"№: {ticket_id}\n"
            f"📅 {data['date']}\n"
            f"🏙 {data['city']}\n"
            f"💺 {data['seat']}\n"
            f"🕒 {data['time']}"
        )
    )
    
    # Небольшая пауза и удаление временного файла, чтобы не копились
    await asyncio.sleep(1)
    if os.path.exists(file_path):
        os.remove(file_path)


@dp.message(F.text == "Мои билеты")
async def my_tickets(message: Message):
    cursor.execute(
        "SELECT id FROM tickets WHERE user_id=? AND is_sold=1",
        (message.from_user.id,)
    )
    tickets = cursor.fetchall()

    if not tickets:
        await message.answer("У вас нет билетов.")
        return

    kb = [[InlineKeyboardButton(
        text=f"Вернуть билет №{t[0]}",
        callback_data=f"return_{t[0]}"
    )] for t in tickets]

    await message.answer(
        "Ваши билеты:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


@dp.callback_query(F.data.startswith("return_"))
async def return_ticket(callback: CallbackQuery):
    ticket_id = callback.data.split("_")[1]

    cursor.execute(
        "UPDATE tickets SET is_sold=0, user_id=NULL WHERE id=?",
        (ticket_id,)
    )
    conn.commit()

    await callback.message.answer(f"Билет №{ticket_id} возвращён 🔄")


async def main():
    # Запуск планировщика
    try:
        start_scheduler()
    except Exception as e:
        print(f"Ошибка планировщика: {e}")
        
    print("Бот успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
