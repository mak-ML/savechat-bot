from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards import main_menu, search_keyboard
from utils import logger, sanitize_input

router = Router()

class SearchStates(StatesGroup):
    waiting_for_query = State()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я буду сохранять все твои сообщения и отслеживать удалённые.\n\n"
        "Просто пересылай мне сообщения или добавь меня в группу.",
        reply_markup=main_menu()
    )

@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    stats = await db.get_user_stats(message.from_user.id)
    
    text = (
        f"📊 <b>Твоя статистика:</b>\n\n"
        f"💬 Всего сообщений: {stats['total']}\n"
        f"🗑 Удалённых: {stats['deleted']}\n"
    )
    
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🔍 Поиск")
async def search_start(message: Message, state: FSMContext):
    await message.answer(
        "🔍 Введите текст для поиска:",
        reply_markup=search_keyboard()
    )
    await state.set_state(SearchStates.waiting_for_query)

@router.message(SearchStates.waiting_for_query)
async def search_process(message: Message, state: FSMContext):
    query = sanitize_input(message.text, max_length=100)
    
    if len(query) < 3:
        await message.answer("❌ Запрос должен быть длиннее 3 символов.")
        return
    
    results = await db.search_messages(message.from_user.id, query)
    
    if not results:
        await message.answer("🔍 Ничего не найдено.")
        await state.clear()
        return
    
    text = f"🔍 <b>Найдено {len(results)} сообщений:</b>\n\n"
    
    for msg in results[:10]:
        status = "🗑" if msg['is_deleted'] else "✅"
        msg_text = msg['text'][:50] + "..." if msg['text'] and len(msg['text']) > 50 else msg['text']
        text += f"{status} {msg_text}\n"
    
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu())
    await state.clear()

@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    text = (
        "<b>ℹ️ Как использовать бота:</b>\n\n"
        "1. Пересылайте сообщения боту\n"
        "2. Добавьте бота в группу\n"
        "3. Бот автоматически сохранит все сообщения\n"
        "4. Если сообщение удалят - вы получите уведомление\n\n"
        "<b>Команды:</b>\n"
        "/start - Главное меню\n"
        "/stats - Статистика\n"
        "/search - Поиск по сообщениям"
    )
    await message.answer(text, parse_mode="HTML")