"""User-facing handlers — messages forwarded to admin."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

import database as db
from config import ADMIN_IDS
from services import notify_admin_new_message

router = Router()


@router.message(Command("start"), ~F.from_user.id.in_(ADMIN_IDS))
async def user_start(message: Message):
    user = message.from_user
    await db.upsert_user(user.id, user.username, user.first_name, user.last_name)
    await message.answer(
        "👋 <b>Welcome to VeyraSupport!</b>\n\n"
        "Write your question or message here — "
        "a support agent will reply shortly.\n\n"
        "Just send any text to get started.",
    )


@router.message(~F.from_user.id.in_(ADMIN_IDS))
async def user_message(message: Message):
    user = message.from_user
    text = message.text or message.caption

    if not text:
        await message.answer("Please send a text message.")
        return

    await db.upsert_user(user.id, user.username, user.first_name, user.last_name)
    await db.add_message(user.id, text, from_admin=False)

    await message.answer(
        "✅ Message received. We'll get back to you soon!",
    )

    user_info = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
    await notify_admin_new_message(message.bot, user.id, text, user_info)
