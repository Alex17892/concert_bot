import asyncio
import qrcode
import io
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile
)
from aiogram.filters import CommandStart
from config import BOT_TOKEN
# Импортируем только функцию подключения из database.py
from database import get_connection, cities, times 
from scheduler import start_scheduler
from keyboards.main_kb import main_kb

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Временное хранилище выбора пользователя (в идеале заменить на FSM)
user_state = {}

def calendar_keyboard():
    kb = []
    for i in range(7):
        day = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        kb.append([InlineKeyboardButton(text=day, callback_data=f"date_{day}")])
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
    
    kb = [[InlineKeyboardButton(text=city, callback_data=f"city_{city}")] for city in cities.keys()]
    await callback.message.edit_text("Выберите город:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("city_"))
async def choose_seat(callback: CallbackQuery):
    city = callback.data.split("_")[1]
    user_state[callback.from_user.id]["city"] = city
    
    seats = cities[city]
    kb = [[InlineKeyboardButton(text=seat, callback_data=f"seat_{seat}")] for seat in seats]
    await callback.message.edit_text("Выберите место:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("seat_"))
async def choose_time(callback: CallbackQuery):
    seat = callback.data.split("_")[1]
    user_state[callback.from_user.id]["seat"] = seat
    
    kb = [[InlineKeyboardButton(text=t, callback_data=f"time_{t}")] for t in times]
    await callback.message.edit_text("Выберите время:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("time_"))
async def buy_ticket(callback: CallbackQuery):
    time_choice = callback.data.split("_")[1]
    user_id = callback.from_user.id
    data = user_state.get(user_id)
    
    if not data:
        await callback.message.answer("Сессия истекла, начните заново.")
        return

    # Работаем с БД через контекстный менеджер (безопасно для потоков)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM tickets 
            WHERE date=? AND city=? AND seat=? AND time=? AND is_sold=0 
            LIMIT 1
        """, (data["date"], data["city"], data["seat"], time_choice))
        
        ticket = cursor.fetchone()
        if not ticket:
            await callback.message.answer("Билет уже продан ❌")
            return

        ticket_id = ticket[0]
        cursor.execute("UPDATE tickets SET is_sold=1, user_id=? WHERE id=?", (user_id, ticket_id))
        conn.commit()

    # Генерация QR в памяти (не создает файлов на диске)
    qr_text = f"Билет №{ticket_id}\nДата: {data['date']}\nГород: {data['city']}\nМесто: {data['seat']}\nВремя: {time_choice}"
    
    qr_img = qrcode.make(qr_text)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)
    
    photo = BufferedInputFile(buffer.read(), filename=f"ticket_{ticket_id}.png")

    await callback.message.answer_photo(
        photo=photo,
        caption=f"🎟 Ваш билет\n\n№: {ticket_id}\n📅 {data['date']}\n🏙 {data['city']}\n💺 {data['seat']}\n🕒 {time_choice}"
    )

@dp.message(F.text == "Мои билеты")
async def my_tickets(message: Message):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tickets WHERE user_id=? AND is_sold=1", (message.from_user.id,))
        tickets = cursor.fetchall()

    if not tickets:
        await message.answer("У вас нет билетов.")
        return

    kb = [[InlineKeyboardButton(text=f"Вернуть билет №{t[0]}", callback_data=f"return_{t[0]}")] for t in tickets]
    await message.answer("Ваши билеты:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("return_"))
async def return_ticket(callback: CallbackQuery):
    ticket_id = callback.data.split("_")[1]
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tickets SET is_sold=0, user_id=NULL WHERE id=?", (ticket_id,))
        conn.commit()
    await callback.message.answer("Билет возвращён 🔄")

async def main():
    start_scheduler()
    print("Бот запущен и планировщик работает!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
