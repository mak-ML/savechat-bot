from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Статистика"), KeyboardButton(text="🔍 Поиск")],
            [KeyboardButton(text="Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard

def search_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
        ]
    )
    return keyboard