from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards import admin_menu, back_to_admin, pagination_keyboard
from utils import logger, validate_sql_query, is_valid_user_id
import config

router = Router()

class AdminStates(StatesGroup):
    waiting_for_sql = State()
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()

async def check_admin(user_id: int) -> bool:
    return await db.is_admin(user_id)

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not await check_admin(message.from_user.id):
        await message.answer("🚫 У вас нет доступа.")
        return
    
    await message.answer(
        "🔐 <b>Админ-панель</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        await callback.answer("🚫 Доступ запрещён", show_alert=True)
        return
    
    stats = await db.get_bot_stats()
    
    text = (
        f"📊 <b>Статистика бота:</b>\n\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"💬 Сообщений: {stats['total_messages']}\n"
        f"🗑 Удалённых: {stats['deleted_messages']}\n"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_to_admin()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        await callback.answer("🚫 Доступ запрещён", show_alert=True)
        return
    
    users = await db.get_all_users(limit=10)
    
    if not users:
        await callback.message.edit_text(
            "👥 Пользователи не найдены",
            reply_markup=back_to_admin()
        )
        return
    
    text = "👥 <b>Список пользователей:</b>\n\n"
    
    for user in users:
        status = "🚫" if user['is_banned'] else "✅"
        text += (
            f"{status} <b>{user['first_name']}</b> (@{user['username'] or 'none'})\n"
            f"ID: <code>{user['user_id']}</code>\n"
            f"Сообщений: {user['message_count']}\n\n"
        )
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_to_admin()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_sql")
async def admin_sql_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("🚫 Доступ запрещён", show_alert=True)
        return
    
    await callback.message.edit_text(
        "💾 <b>SQL запрос</b>\n\n"
        "Введите SELECT запрос (только чтение):\n\n"
        "Пример:\n<code>SELECT * FROM users LIMIT 5;</code>",
        parse_mode="HTML",
        reply_markup=back_to_admin()
    )
    await state.set_state(AdminStates.waiting_for_sql)
    await callback.answer()

@router.message(AdminStates.waiting_for_sql)
async def admin_sql_execute(message: Message, state: FSMContext):
    if not await check_admin(message.from_user.id):
        return
    
    query = message.text.strip()
    
    if not validate_sql_query(query):
        await message.answer(
            "❌ Запрещённый запрос. Разрешены только SELECT.",
            reply_markup=back_to_admin()
        )
        await state.clear()
        return
    
    try:
        results = await db.execute_read_query(query)
        
        if not results:
            await message.answer("📭 Результатов нет", reply_markup=back_to_admin())
        else:
            text = f"✅ <b>Найдено записей: {len(results)}</b>\n\n"
            
            for i, row in enumerate(results[:5], 1):
                text += f"<b>{i}.</b> {row}\n\n"
            
            if len(results) > 5:
                text += f"... и ещё {len(results) - 5} записей"
            
            await message.answer(text, parse_mode="HTML", reply_markup=back_to_admin())
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"SQL error: {e}")
        await message.answer(
            f"❌ Ошибка выполнения:\n<code>{str(e)}</code>",
            parse_mode="HTML",
            reply_markup=back_to_admin()
        )
        await state.clear()

@router.callback_query(F.data == "admin_ban")
async def admin_ban_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("🚫 Доступ запрещён", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🚫 <b>Бан пользователя</b>\n\n"
        "Отправьте команду:\n"
        "/ban [user_id] - заблокировать\n"
        "/unban [user_id] - разблокировать",
        parse_mode="HTML",
        reply_markup=back_to_admin()
    )
    await callback.answer()

@router.message(Command("ban"))
async def ban_user_cmd(message: Message):
    if not await check_admin(message.from_user.id):
        return
    
    try:
        user_id = int(message.text.split()[1])
        
        if not is_valid_user_id(user_id):
            await message.answer("❌ Некорректный ID")
            return
        
        if user_id in config.ADMIN_IDS:
            await message.answer("❌ Нельзя забанить админа")
            return
        
        await db.ban_user(user_id)
        await message.answer(f"✅ Пользователь {user_id} заблокирован")
        
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /ban [user_id]")

@router.message(Command("unban"))
async def unban_user_cmd(message: Message):
    if not await check_admin(message.from_user.id):
        return
    
    try:
        user_id = int(message.text.split()[1])
        
        if not is_valid_user_id(user_id):
            await message.answer("❌ Некорректный ID")
            return
        
        await db.unban_user(user_id)
        await message.answer(f"✅ Пользователь {user_id} разблокирован")
        
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /unban [user_id]")

@router.callback_query(F.data == "back_to_admin")
async def back_to_admin_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🔐 <b>Админ-панель</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_close")
async def close_admin_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()