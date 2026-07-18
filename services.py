"""Shared helpers for admin notifications."""

from config import ADMIN_IDS
from keyboards import open_chat_kb


def display_name(user: dict) -> str:
    if user.get("username"):
        return f"@{user['username']}"
    parts = [user.get("first_name") or "", user.get("last_name") or ""]
    return " ".join(p for p in parts if p).strip() or f"ID {user['user_id']}"


async def notify_admin_new_message(bot, user_id: int, text: str, user_info: dict):
    name = display_name(user_info)
    preview = text[:200] + ("…" if len(text) > 200 else "")

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"📩 <b>New message</b>\n"
                f"From: <b>{name}</b>\n"
                f"<code>ID: {user_id}</code>\n\n"
                f"{preview}",
                reply_markup=open_chat_kb(user_id),
            )
        except Exception:
            pass
