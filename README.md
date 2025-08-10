
# Telegram Chat Liveness Checker Suite

Набор скриптов для массового анализа «жизни» Telegram-чатов и подготовки чистых списков ссылок.

---

## 📦 Содержимое репозитория

- **`.env.example`**  
  Пример файла с настройками (скопируйте в `.env` и заполните своими значениями).

- **`filter_telegram_chats.py`**  
  Основной скрипт. По списку чатов проверяет каждый чат/канал по критериям:
  1. **минимум участников** (`MIN_PARTICIPANTS`)
  2. **свежесть** — последний пост не старше `RECENT_DAYS` дней
  3. **активность** — не более `MAX_MSG_COUNT` сообщений от пользователей за последние `MSG_PERIOD_SECONDS` секунд
  4. **минимум онлайн** (`MIN_ONLINE`)
  5. **игнор сервисных сообщений** (join/leave/pin/invite и т. п.)
  
  Результат:
  - `active_chats.txt` — «живые» чаты  
  - `inactive_chats.txt` — «мертвые» чаты

- **`extract_links.py`**  
  Извлекает из любого отчёта (по умолчанию `active_chats.txt`) все ссылки `https://t.me/...` → `active_links.txt`.

- **`strip_numbering.py`**  
  Убирает префиксы вида `123.` или `123. ` → оставляет только URL  
  (вход — `active_links.txt`, выход — `links_clean.txt`).

- **`chats.txt`**  
  Список чатов (по одному на строку). Допустимые форматы:  
  `@username`, `username`, `https://t.me/username`, `t.me/username`, а также инвайт-ссылки `https://t.me/+...` / `joinchat/...`.

---

## ⚙️ Установка и настройка

```bash
git clone https://github.com/k2wGG/Telegram-Chat-Liveness-Checker-Suite.git
cd Telegram-Chat-Liveness-Checker-Suite

python -m venv venv
# Windows/Git-bash:
source venv/Scripts/activate
# macOS/Linux:
source venv/bin/activate

pip install telethon python-dotenv
````

Скопируйте `.env.example` → `.env` и заполните.

### Пример `.env`

```dotenv
# Ваши Telegram API-ключи (https://my.telegram.org)
API_ID=123456
API_HASH=abcdef123456

# Если хотите логиниться как бот (не рекомендуется из-за ограничений):
# BOT_TOKEN=123456789:ABCdefGhIjklMnop

# Для user-mode
PHONE=+71234567890
# Имя файла сессии (по умолчанию session_user)
SESSION_NAME=session_user

# Пороговые значения для «живых» чатов
MIN_PARTICIPANTS=2000    # минимум участников в чате
MIN_ONLINE=300           # минимум одновременно онлайн
MSG_PERIOD_SECONDS=60    # интервал в секундах для подсчёта сообщений
MAX_MSG_COUNT=15         # максимально допустимое число сообщений за период
RECENT_DAYS=180          # проверка «свежести» последнего сообщения (не старее этого числа дней)

# Файлы ввода/вывода
INPUT_FILE=chats.txt
ACTIVE_FILE=active_chats.txt
INACTIVE_FILE=inactive_chats.txt

# (опционально) Можно передать чаты прямо здесь. Либо многострочно, либо через запятую.
# Примеры (любой один вариант):
# CHATS=@BabyNeoGroup
# CHATS=@BabyNeoGroup,dailyairdropcomboonly,https://t.me/aplicatiireferrals,t.me/Com_00111
# CHATS="@BabyNeoGroup
# dailyairdropcomboonly
# https://t.me/aplicatiireferrals
# t.me/Com_00111"

# Формат вывода идентификаторов в результатах:
# raw — не менять; at — @username; url — https://t.me/username
OUTPUT_FORMAT=at
```

> Если указана переменная `CHATS`, список берётся из неё и файл `INPUT_FILE` игнорируется.
> Скрипт понимает любые форматы идентификаторов и сам «нормализует» их перед проверкой.

---

## 🚀 Использование

### 1) Проверка чатов

```bash
python filter_telegram_chats.py
```

**User-mode**
При первом запуске введите телефон → код из Telegram (обычно приходит в «Telegram» чат) → при необходимости пароль 2FA.
Сессия сохранится в `SESSION_NAME.session` и на следующих запусках код не потребуется.

**Bot-mode**
Если в `.env` указан `BOT_TOKEN`, запуск без телефона и кода.
Важно: бот должен быть добавлен во все чаты/каналы и иметь право **Read history**.

**Результаты**

* `active_chats.txt` — список «живых» чатов в формате, заданном `OUTPUT_FORMAT`
* `inactive_chats.txt` — список «мертвых» чатов в том же формате

### 2) Извлечение ссылок

```bash
python extract_links.py
# По умолчанию: active_chats.txt -> active_links.txt
```

### 3) Удаление нумерации

```bash
python strip_numbering.py
# По умолчанию: active_links.txt -> links_clean.txt
```

---

## 🔍 Пример конвейера

```bash
# 1) Проверка и разметка «живых/мертвых»
python filter_telegram_chats.py

# 2) Достаём из «живых» только URL
python extract_links.py active_chats.txt active_links.txt

# 3) Убираем нумерацию (если нужна)
python strip_numbering.py active_links.txt links_clean.txt
```

---

## ❓ FAQ

**Где взять API\_ID и API\_HASH?**
На [https://my.telegram.org](https://my.telegram.org) → «API Development Tools».

**Код не приходит по SMS — что делать?**
Код обычно приходит в официальный чат «Telegram» внутри приложения. Проверьте там.

**Скрипт снова просит код при каждом запуске.**
Запускайте из той же папки, где лежит файл сессии `SESSION_NAME.session`, и не удаляйте его.

**Почему в результатах нет `@`?**
Поставьте `OUTPUT_FORMAT=at` (или `url`) в `.env`. По умолчанию стоит `at`.

**Бот ничего не видит.**
Проверьте, что бот добавлен в чаты и имеет право читать историю сообщений.
