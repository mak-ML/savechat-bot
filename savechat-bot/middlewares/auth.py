from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from database import db
from utils import logger

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        
        await db.add_user(user.id, user.username, user.first_name)
        
        if await db.is_user_banned(user.id):
            await event.answer("Вы заблокированы.")
            return
        
        return await handler(event, data)