import os
import re
import asyncio
from datetime import datetime, timedelta

from telethon import TelegramClient, errors, types, functions
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# ====== .env ======
load_dotenv()
API_ID_RAW = os.getenv('API_ID')
API_HASH   = os.getenv('API_HASH')
if not API_ID_RAW or not API_HASH:
    raise SystemExit("❌ В .env должны быть API_ID и API_HASH")
API_ID   = int(API_ID_RAW)
BOT_TOKEN = os.getenv('BOT_TOKEN')
PHONE     = os.getenv('PHONE')
SESSION_NAME = os.getenv('SESSION_NAME', 'session_user')

# Пороги
def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == '':
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"[WARN] {name}='{raw}' не число. Использую {default}.")
        return default

MIN_PARTICIPANTS   = env_int('MIN_PARTICIPANTS', 2000)
MIN_ONLINE         = env_int('MIN_ONLINE', 300)
MSG_PERIOD_SECONDS = env_int('MSG_PERIOD_SECONDS', 60)
MAX_MSG_COUNT      = env_int('MAX_MSG_COUNT', 15)
RECENT_DAYS        = env_int('RECENT_DAYS', 365)

# Файлы / ввод
INPUT_FILE    = os.getenv('INPUT_FILE', 'chats.txt')
ACTIVE_FILE   = os.getenv('ACTIVE_FILE', 'active_chats.txt')
INACTIVE_FILE = os.getenv('INACTIVE_FILE', 'inactive_chats.txt')
CHATS_INLINE  = os.getenv('CHATS')  # опционально: список чатов прямо в .env
OUTPUT_FORMAT = os.getenv('OUTPUT_FORMAT', 'at').lower()  # raw | at | url

# ====== helpers ======
def normalize_id(s: str) -> str:
    s = s.strip()
    if not s or s.startswith('#'):
        return ''
    if s.startswith('@'):
        s = s[1:]
    if s.startswith('t.me/'):
        s = 'https://' + s
    return s

def chats_from_env(raw: str):
    if not raw:
        return None
    parts = re.split(r'[,\n; ]+', raw)
    out, seen = [], set()
    for p in parts:
        x = normalize_id(p)
        if x and x not in seen:
            out.append(x)
            seen.add(x)
    return out

def load_chat_list(path):
    if CHATS_INLINE:
        env_list = chats_from_env(CHATS_INLINE)
        if env_list:
            return env_list
    ids, seen = [], set()
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            x = normalize_id(line)
            if x and x not in seen:
                ids.append(x)
                seen.add(x)
    return ids

def format_for_output(ident: str) -> str:
    """Преобразуем вывод по желаемому формату."""
    if OUTPUT_FORMAT == 'raw':
        return ident
    if OUTPUT_FORMAT == 'at':
        # если это URL вида https://t.me/username — превратим в @username
        m = re.fullmatch(r'https?://t\.me/([A-Za-z0-9_]+)', ident)
        if m:
            return '@' + m.group(1)
        # если «голый» username — добавим @
        if not ident.startswith('http'):
            return '@' + ident.lstrip('@')
        return ident
    if OUTPUT_FORMAT == 'url':
        # если «голый» username — превратим в https://t.me/username
        if not ident.startswith('http'):
            return 'https://t.me/' + ident.lstrip('@')
        return ident
    return ident

async def ensure_user_login(client: TelegramClient):
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

        # Инфо о чате/канале
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

        # Свежесть последнего сообщения
        history = await client.get_messages(entity, limit=1)
        last_date = history[0].date.replace(tzinfo=None) if history else None
        if not last_date or last_date < datetime.utcnow() - timedelta(days=RECENT_DAYS):
            return chat_identifier, False

        # Сообщения за период (только пользовательские)
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

# ====== main ======
async def main(input_file):
    chats = load_chat_list(input_file)

    if BOT_TOKEN:
        client = TelegramClient('session_bot', API_ID, API_HASH)
        await client.start(bot_token=BOT_TOKEN)
    else:
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await ensure_user_login(client)

    active, inactive = [], []
    for chat in chats:
        print(f"Checking {chat}...")
        ident, is_active = await check_chat(client, chat)
        (active if is_active else inactive).append(ident)

    with open(ACTIVE_FILE, 'w', encoding='utf-8') as fa:
        for ident in active:
            fa.write(format_for_output(ident) + "\n")
    with open(INACTIVE_FILE, 'w', encoding='utf-8') as fi:
        for ident in inactive:
            fi.write(format_for_output(ident) + "\n")

    print(f"Checked {len(chats)} chats. Active: {len(active)}, Inactive: {len(inactive)}.")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main(INPUT_FILE))
