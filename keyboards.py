"""Inline and reply keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from config import MESSAGES_PER_PAGE


def admin_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Chats")],
            [KeyboardButton(text="ℹ️ Help")],
        ],
        resize_keyboard=True,
    )


def chats_list_kb(chats: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    start = page * MESSAGES_PER_PAGE
    chunk = chats[start : start + MESSAGES_PER_PAGE]
    buttons = []

    for chat in chunk:
        label = _chat_label(chat)
        buttons.append([
            InlineKeyboardButton(
                text=label,
                callback_data=f"open:{chat['user_id']}",
            )
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="← Prev", callback_data=f"page:{page - 1}"))
    if start + MESSAGES_PER_PAGE < len(chats):
        nav.append(InlineKeyboardButton(text="Next →", callback_data=f"page:{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="↩ Close", callback_data="close")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def chat_actions_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="← Back to chats", callback_data="back_chats"),
                InlineKeyboardButton(text="🗑 Delete chat", callback_data=f"delete:{user_id}"),
            ],
        ]
    )


def confirm_delete_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yes, delete", callback_data=f"confirm_del:{user_id}"),
                InlineKeyboardButton(text="❌ Cancel", callback_data=f"open:{user_id}"),
            ],
        ]
    )


def open_chat_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Open chat", callback_data=f"open:{user_id}")],
        ]
    )


def _chat_label(chat: dict) -> str:
    name = chat.get("first_name") or "User"
    if chat.get("username"):
        name = f"@{chat['username']}"
    preview = (chat.get("last_message") or "")[:28]
    if len(chat.get("last_message") or "") > 28:
        preview += "…"
    prefix = "↩ " if chat.get("last_from_admin") else "→ "
    return f"{prefix}{name}: {preview}"
