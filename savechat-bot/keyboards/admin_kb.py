from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика бота", callback_data="admin_stats")],
            [InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users")],
            [InlineKeyboardButton(text="💾 SQL запрос", callback_data="admin_sql")],
            [InlineKeyboardButton(text="🚫 Бан/Разбан", callback_data="admin_ban")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")]
        ]
    )
    return keyboard

def back_to_admin():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin")]
        ]
    )
    return keyboard

def pagination_keyboard(page: int, total_pages: int, prefix: str):
    buttons = []
    
    if page > 1:
        buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"{prefix}_{page-1}"))
    
    buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"{prefix}_{page+1}"))
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            buttons,
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin")]
        ]
    )
    return keyboard