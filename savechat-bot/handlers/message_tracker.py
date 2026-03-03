from aiogram import Router, F
from aiogram.types import Message, MessageReactionUpdated
from database import db
from utils import logger

router = Router()

@router.message(F.text)
async def track_text_message(message: Message):
    if message.chat.type == "private":
        if message.forward_from or message.forward_from_chat:
            await db.save_message(
                user_id=message.from_user.id,
                chat_id=message.forward_from_chat.id if message.forward_from_chat else message.forward_from.id,
                message_id=message.forward_id or message.message_id,
                text=message.text
            )
            await message.answer("✅ Сообщение сохранено")
        else:
            await db.save_message(
                user_id=message.from_user.id,
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=message.text
            )
    else:
        await db.save_message(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=message.text
        )

@router.message(F.photo)
async def track_photo_message(message: Message):
    await db.save_message(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=message.caption,
        media_type="photo",
        media_file_id=message.photo[-1].file_id
    )

@router.message(F.video)
async def track_video_message(message: Message):
    await db.save_message(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=message.caption,
        media_type="video",
        media_file_id=message.video.file_id
    )

@router.message(F.document)
async def track_document_message(message: Message):
    await db.save_message(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=message.caption,
        media_type="document",
        media_file_id=message.document.file_id
    )

@router.message(F.voice)
async def track_voice_message(message: Message):
    await db.save_message(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        message_id=message.message_id,
        media_type="voice",
        media_file_id=message.voice.file_id
    )