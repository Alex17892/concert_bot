from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Главное меню
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Выбрать день")],
        [KeyboardButton(text="Мои билеты")]
    ],
    resize_keyboard=True
)