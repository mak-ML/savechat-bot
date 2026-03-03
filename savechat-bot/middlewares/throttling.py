from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
import redis.asyncio as redis
import config
from utils import logger

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self.redis = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            decode_responses=True
        )

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        key = f"throttle:{user_id}:message"
        
        current = await self.redis.get(key)
        
        if current and int(current) >= config.RATE_LIMIT:
            await event.answer("Слишком много запросов. Подождите немного.")
            return
        
        await self.redis.incr(key)
        await self.redis.expire(key, config.RATE_LIMIT_TIME)
        
        return await handler(event, data)