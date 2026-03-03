import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
import config
from utils import logger

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                host=config.POSTGRES_HOST,
                port=config.POSTGRES_PORT,
                database=config.POSTGRES_DB,
                user=config.POSTGRES_USER,
                password=config.POSTGRES_PASSWORD,
                min_size=5,
                max_size=20
            )
            await self.create_tables()
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("Database connection closed")

    async def create_tables(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    is_premium BOOLEAN DEFAULT FALSE,
                    is_banned BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    chat_id BIGINT,
                    message_id INTEGER,
                    text TEXT,
                    media_type VARCHAR(50),
                    media_file_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    UNIQUE(chat_id, message_id)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS deleted_messages (
                    id SERIAL PRIMARY KEY,
                    original_message_id INTEGER REFERENCES messages(id),
                    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id BIGINT PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)
            """)

    async def add_user(self, user_id: int, username: Optional[str], first_name: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username, first_name)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE
                SET username = $2, first_name = $3
            """, user_id, username, first_name)

    async def get_user(self, user_id: int) -> Optional[Dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1", user_id
            )
            return dict(row) if row else None

    async def is_user_banned(self, user_id: int) -> bool:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT is_banned FROM users WHERE user_id = $1", user_id
            )
            return result or False

    async def ban_user(self, user_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET is_banned = TRUE WHERE user_id = $1", user_id
            )

    async def unban_user(self, user_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET is_banned = FALSE WHERE user_id = $1", user_id
            )

    async def save_message(
        self, 
        user_id: int, 
        chat_id: int, 
        message_id: int,
        text: Optional[str] = None,
        media_type: Optional[str] = None,
        media_file_id: Optional[str] = None
    ) -> int:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("""
                INSERT INTO messages (user_id, chat_id, message_id, text, media_type, media_file_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (chat_id, message_id) DO UPDATE
                SET text = $4, media_type = $5, media_file_id = $6
                RETURNING id
            """, user_id, chat_id, message_id, text, media_type, media_file_id)
            return result

    async def mark_message_deleted(self, chat_id: int, message_id: int):
        async with self.pool.acquire() as conn:
            msg_id = await conn.fetchval("""
                UPDATE messages 
                SET is_deleted = TRUE 
                WHERE chat_id = $1 AND message_id = $2
                RETURNING id
            """, chat_id, message_id)
            
            if msg_id:
                await conn.execute("""
                    INSERT INTO deleted_messages (original_message_id)
                    VALUES ($1)
                """, msg_id)

    async def search_messages(self, user_id: int, query: str, limit: int = 20) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM messages 
                WHERE user_id = $1 AND text ILIKE $2
                ORDER BY created_at DESC
                LIMIT $3
            """, user_id, f"%{query}%", limit)
            return [dict(row) for row in rows]

    async def get_user_stats(self, user_id: int) -> Dict[str, int]:
        async with self.pool.acquire() as conn:
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM messages WHERE user_id = $1", user_id
            )
            deleted = await conn.fetchval(
                "SELECT COUNT(*) FROM messages WHERE user_id = $1 AND is_deleted = TRUE", user_id
            )
            return {"total": total or 0, "deleted": deleted or 0}

    async def get_all_users(self, limit: int = 100) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT u.*, COUNT(m.id) as message_count
                FROM users u
                LEFT JOIN messages m ON u.user_id = m.user_id
                GROUP BY u.user_id
                ORDER BY u.created_at DESC
                LIMIT $1
            """, limit)
            return [dict(row) for row in rows]

    async def get_bot_stats(self) -> Dict[str, int]:
        async with self.pool.acquire() as conn:
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
            total_messages = await conn.fetchval("SELECT COUNT(*) FROM messages")
            deleted_messages = await conn.fetchval(
                "SELECT COUNT(*) FROM messages WHERE is_deleted = TRUE"
            )
            return {
                "total_users": total_users or 0,
                "total_messages": total_messages or 0,
                "deleted_messages": deleted_messages or 0
            }

    async def execute_read_query(self, query: str) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def is_admin(self, user_id: int) -> bool:
        if user_id in config.ADMIN_IDS:
            return True
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT user_id FROM admins WHERE user_id = $1", user_id
            )
            return result is not None

    async def add_admin(self, user_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO admins (user_id) VALUES ($1) ON CONFLICT DO NOTHING", 
                user_id
            )

db = Database()