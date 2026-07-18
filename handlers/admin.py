"""Admin panel: chat list, reply mode, delete."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database as db
from config import ADMIN_IDS, HISTORY_LIMIT
from keyboards import (
    admin_main_kb,
    chat_actions_kb,
    chats_list_kb,
    confirm_delete_kb,
)
from services import display_name

router = Router()


class AdminReply(StatesGroup):
    in_chat = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def format_history(history: list[dict]) -> str:
    if not history:
        return "<i>No messages yet.</i>"
    lines = []
    for msg in history:
        side = "🟠 You" if msg["from_admin"] else "⚪ User"
        lines.append(f"{side}: {msg['text']}")
    return "\n\n".join(lines)


@router.message(Command("start"), F.from_user.id.in_(ADMIN_IDS))
async def admin_start(message: Message, state: FSMContext):
    await state.clear()
    count = await db.chat_count()
    await message.answer(
        f"<b>VeyraSupport — Admin Panel</b>\n\n"
        f"Active chats: <b>{count}</b>\n\n"
        f"Tap <b>💬 Chats</b> to see user conversations.\n"
        f"Open a chat and reply — your messages go directly to the user.",
        reply_markup=admin_main_kb(),
    )


@router.message(F.text == "ℹ️ Help", F.from_user.id.in_(ADMIN_IDS))
async def admin_help(message: Message):
    await message.answer(
        "<b>How it works</b>\n\n"
        "1. Users write to the bot\n"
        "2. You get a notification with their message\n"
        "3. Open <b>💬 Chats</b> → pick a user\n"
        "4. Reply in the chat — bot forwards your text\n"
        "5. <b>← Back</b> exits the chat\n"
        "6. <b>🗑 Delete</b> removes the chat from your list\n\n"
        "While inside a chat, every message you send goes to that user.",
    )


@router.message(F.text == "💬 Chats", F.from_user.id.in_(ADMIN_IDS))
async def show_chats(message: Message, state: FSMContext):
    await state.clear()
    await _send_chats_list(message, page=0)


@router.callback_query(F.data.startswith("page:"), F.from_user.id.in_(ADMIN_IDS))
async def chats_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    chats = await db.list_active_chats()
    if not chats:
        await callback.message.edit_text("No active chats yet.")
        await callback.answer()
        return
    await callback.message.edit_text(
        f"<b>Active chats</b> ({len(chats)})\n\nTap a chat to open:",
        reply_markup=chats_list_kb(chats, page),
    )
    await callback.answer()


@router.callback_query(F.data == "back_chats", F.from_user.id.in_(ADMIN_IDS))
async def back_to_chats(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    chats = await db.list_active_chats()
    if not chats:
        await callback.message.edit_text("No active chats.")
    else:
        await callback.message.edit_text(
            f"<b>Active chats</b> ({len(chats)})\n\nTap a chat to open:",
            reply_markup=chats_list_kb(chats),
        )
    await callback.answer("Back to chat list")


@router.callback_query(F.data == "close", F.from_user.id.in_(ADMIN_IDS))
async def close_list(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("open:"), F.from_user.id.in_(ADMIN_IDS))
async def open_chat(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[1])
    user = await db.get_user(user_id)
    if not user:
        await callback.answer("Chat not found or deleted.", show_alert=True)
        return

    await state.set_state(AdminReply.in_chat)
    await state.update_data(reply_to=user_id)

    history = await db.get_history(user_id, HISTORY_LIMIT)
    name = display_name(user)

    await callback.message.edit_text(
        f"<b>Chat with {name}</b>\n"
        f"<code>ID: {user_id}</code>\n\n"
        f"{format_history(history)}\n\n"
        f"<i>Reply below — your messages will be sent to this user.</i>",
        reply_markup=chat_actions_kb(user_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete:"), F.from_user.id.in_(ADMIN_IDS))
async def delete_prompt(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    user = await db.get_user(user_id)
    name = display_name(user) if user else f"ID {user_id}"
    await callback.message.edit_text(
        f"Delete chat with <b>{name}</b>?\n\n"
        f"The user can still write again — that will create a new chat.",
        reply_markup=confirm_delete_kb(user_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_del:"), F.from_user.id.in_(ADMIN_IDS))
async def confirm_delete(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[1])
    await db.delete_chat(user_id)
    await state.clear()

    chats = await db.list_active_chats()
    if chats:
        await callback.message.edit_text(
            f"Chat deleted.\n\n<b>Active chats</b> ({len(chats)}):",
            reply_markup=chats_list_kb(chats),
        )
    else:
        await callback.message.edit_text("Chat deleted. No active chats left.")
    await callback.answer("Chat deleted")


@router.message(AdminReply.in_chat, F.from_user.id.in_(ADMIN_IDS))
async def admin_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_to")
    if not user_id:
        await state.clear()
        return

    text = message.text or message.caption
    if not text:
        await message.answer("Send text messages only while in a chat.")
        return

    await db.add_message(user_id, text, from_admin=True)

    try:
        await message.bot.send_message(
            user_id,
            f"<b>Support:</b>\n{text}",
        )
    except Exception:
        await message.answer("⚠️ Could not deliver — user may have blocked the bot.")
        return

    await message.answer("✅ Sent", reply_markup=chat_actions_kb(user_id))


async def _send_chats_list(message: Message, page: int = 0):
    chats = await db.list_active_chats()
    if not chats:
        await message.answer("No active chats yet. Waiting for users…")
        return
    await message.answer(
        f"<b>Active chats</b> ({len(chats)})\n\nTap a chat to open:",
        reply_markup=chats_list_kb(chats, page),
    )
