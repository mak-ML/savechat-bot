from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    user_id: int
    username: Optional[str]
    first_name: str
    is_premium: bool = False
    is_banned: bool = False
    created_at: datetime = None

@dataclass
class Message:
    id: int
    user_id: int
    chat_id: int
    message_id: int
    text: Optional[str]
    media_type: Optional[str]
    media_file_id: Optional[str]
    created_at: datetime
    is_deleted: bool = False

@dataclass
class DeletedMessage:
    id: int
    original_message_id: int
    deleted_at: datetime