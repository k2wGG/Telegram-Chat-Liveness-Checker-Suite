# Telegram Chat Liveness Checker Suite

Набор скриптов для массового анализа “жизни” Telegram-чатов, очистки и подготовки списков ссылок.

---

## 📦 Содержимое репозитория

- **`.env.example`**  
  Пример файла с секретными настройками (копируйте или переименуйте в `.env` и заполните свои значения).

- **`filter_telegram_chats.py`**  
  Основной скрипт, который по списку `chats.txt` проверяет каждый канал/чат по таким критериям:  
  1. **Минимум участников** (`MIN_PARTICIPANTS`)  
  2. **Свежесть последнего поста** — есть хотя бы одно сообщение не старше `RECENT_DAYS` дней  
  3. **Не более N сообщений** от реальных пользователей за последние M секунд (`MSG_PERIOD_SECONDS`, `MAX_MSG_COUNT`)  
  4. **Минимум онлайн-участников** (`MIN_ONLINE`)  
  5. **Игнорирует service- и action-сообщения** (присоединения, инвайты и т.п.)  
  Результат записывается в `active_chats.txt` и `inactive_chats.txt`.

- **`extract_links.py`**  
  Берёт любой текстовый отчёт (по умолчанию `active_chats.txt`), ищет в нём ссылки `https://t.me/...` и  
  записывает найденные URL в новый файл (по умолчанию `active_links.txt`).

- **`strip_numbering.py`**  
  Убирает из строк префиксы вида `123.` или `123. `, оставляя только URL.  
  Работает по данным из `active_links.txt` (или любого указанного входного файла).
---

## ⚙️ Установка и настройка

1. **Склонируйте репозиторий**  
   ```bash
   git clone https://github.com/k2wGG/Telegram-Chat-Liveness-Checker-Suite.git
   cd Telegram-Chat-Liveness-Checker-Suite

2. **Создайте виртуальное окружение**

   ```bash
   python -m venv venv
   source venv/Scripts/activate    # Windows/Git-bash
   # или source venv/bin/activate  # macOS/Linux
   ```

3. **Установите зависимости**

   ```bash
   pip install telethon python-dotenv
   ```

4. **Скопируйте `.env.example` → `.env` и заполните**

   ```dotenv
   # — Ваши ключи приложения —
   API_ID=123456
   API_HASH=abcdef123456

   # Бот-токен (если используете бота вместо user-mode, но у ботов есть ограничения) - не советую
   # BOT_TOKEN=123456789:ABCdefGhIjklMnop

   # Для логина через телефон (user-mode)
   PHONE=+71234567890

   # — Пороговые параметры —
   MIN_PARTICIPANTS=2000    # минимум участников в чате
   RECENT_DAYS=180          # не учитывать чаты без постов старше этого числа дней
   MSG_PERIOD_SECONDS=60    # интервал в секундах для подсчёта сообщений
   MAX_MSG_COUNT=15         # макс. сообщений от пользователей за период
   MIN_ONLINE=300           # минимум одновременно онлайн

   # — Файлы ввода/вывода —
   INPUT_FILE=chats.txt
   ACTIVE_FILE=active_chats.txt
   INACTIVE_FILE=inactive_chats.txt
   ```

---

## 🚀 Usage

### 1. `filter_telegram_chats.py`

Проверяет список чатов из `INPUT_FILE` (“chats.txt”) и делит их на «живые» и «мертвые».

```bash
python filter_telegram_chats.py
```

* **User-mode**:
  При первом запуске, если не задан `BOT_TOKEN`, появится запрос `PHONE` → код из Telegram → (опционально) двухфакторный пароль.
  После входа Telethon сохранит `session_user.session` и больше не будет спрашивать код.

* **Bot-mode**:
  Если в `.env` указан `BOT_TOKEN`, скрипт запустится от имени бота (без запроса телефона/кода).
  *Важно*: бот должен быть приглашён во все проверяемые чаты/каналы и иметь право “Read history”.

**Результаты**:

* `active_chats.txt` — список URL «живых» чатов.
* `inactive_chats.txt` — список URL «мертвых» чатов.

---

### 2. `extract_links.py`

Извлекает из текстового отчёта все Telegram-ссылки.

```bash
python extract_links.py
# По умолчанию:
#   input_file  = active_chats.txt
#   output_file = active_links.txt
```

Использует регулярное выражение: `https?://t\.me/\S+`.

---

### 3. `strip_numbering.py`

Удаляет числовые префиксы вида `123.` или `123. ` и оставляет только URL.

```bash
python strip_numbering.py
# По умолчанию:
#   input_file  = active_links.txt
#   output_file = links_clean.txt
```

Регулярка: `^\s*\d+\.\s*(https?://\S+)`.

---

## 🔍 Пример полного конвейера

```bash
# 1) Основная проверка
python filter_telegram_chats.py

# 2) Извлечение ссылок
python extract_links.py active_chats.txt links_with_nums.txt

# 3) Удаление нумерации
python strip_numbering.py links_with_nums.txt links_clean.txt

```
