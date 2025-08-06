import os
import asyncio
from datetime import datetime, timedelta
import sys

from telethon import TelegramClient, errors, types, functions
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Значения из .env
API_ID = int(os.getenv('API_ID'))               # ваш api_id
API_HASH = os.getenv('API_HASH')                # ваш api_hash
BOT_TOKEN = os.getenv('BOT_TOKEN')              # токен бота (опционально)
PHONE = os.getenv('PHONE')                      # номер телефона для логина (для user-mode)

# ============ Пороговые значения ============
MIN_PARTICIPANTS   = int(os.getenv('MIN_PARTICIPANTS', 2000))
MIN_ONLINE         = int(os.getenv('MIN_ONLINE', 300))
MSG_PERIOD_SECONDS = int(os.getenv('MSG_PERIOD_SECONDS', 60))
MAX_MSG_COUNT      = int(os.getenv('MAX_MSG_COUNT', 15))
RECENT_DAYS        = int(os.getenv('RECENT_DAYS', 365))  # дни для проверки свежести

# Файлы
INPUT_FILE    = os.getenv('INPUT_FILE', 'chats.txt')
ACTIVE_FILE   = os.getenv('ACTIVE_FILE', 'active_chats.txt')
INACTIVE_FILE = os.getenv('INACTIVE_FILE', 'inactive_chats.txt')
# =============================================

def load_chat_list(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

async def ensure_user_login(client):
    await client.connect()
    if await client.is_user_authorized():
        return
    phone = PHONE or input('Enter your phone (+...): ')
    await client.send_code_request(phone)
    code = input('Enter code: ')
    try:
        await client.sign_in(phone, code)
    except SessionPasswordNeededError:
        pwd = input('Two-step password: ')
        await client.sign_in(password=pwd)

async def check_chat(client, chat_identifier):
    try:
        entity = await client.get_entity(chat_identifier)

        if isinstance(entity, types.Channel):
            full = await client(functions.channels.GetFullChannelRequest(channel=entity))
            participants = full.full_chat.participants_count
            online = full.full_chat.online_count
        elif isinstance(entity, types.Chat):
            full = await client(functions.messages.GetFullChatRequest(chat_id=entity.id))
            participants = full.full_chat.participants_count
            online = None
        else:
            return chat_identifier, False

        if participants < MIN_PARTICIPANTS:
            return chat_identifier, False

        # Проверка последнего сообщения на свежесть
        history = await client.get_messages(entity, limit=1)
        last_date = history[0].date.replace(tzinfo=None) if history else None
        if not last_date or last_date < datetime.utcnow() - timedelta(days=RECENT_DAYS):
            return chat_identifier, False

        cutoff = datetime.utcnow() - timedelta(seconds=MSG_PERIOD_SECONDS)
        msg_count = 0
        async for msg in client.iter_messages(entity, limit=1000):
            if getattr(msg, 'action', None) or getattr(msg, 'service', False):
                continue
            if msg.date.replace(tzinfo=None) >= cutoff:
                msg_count += 1
                if msg_count > MAX_MSG_COUNT:
                    return chat_identifier, False
            else:
                break

        if online is not None and online < MIN_ONLINE:
            return chat_identifier, False

        return chat_identifier, True
    except Exception:
        return chat_identifier, False

async def main(input_file):
    chats = load_chat_list(input_file)
    if BOT_TOKEN:
        client = TelegramClient('session_bot', API_ID, API_HASH)
        await client.start(bot_token=BOT_TOKEN)
    else:
        client = TelegramClient('session_user', API_ID, API_HASH)
        await ensure_user_login(client)

    active = []
    inactive = []
    for chat in chats:
        print(f"Checking {chat}...")
        ident, is_active = await check_chat(client, chat)
        (active if is_active else inactive).append(ident)

    with open(ACTIVE_FILE, 'w', encoding='utf-8') as fa:
        for ident in active:
            fa.write(f"{ident}\n")
    with open(INACTIVE_FILE, 'w', encoding='utf-8') as fi:
        for ident in inactive:
            fi.write(f"{ident}\n")

    print(f"Checked {len(chats)} chats. Active: {len(active)}, Inactive: {len(inactive)}.")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main(INPUT_FILE))
