# extract_links.py
# Скрипт извлекает только ссылки из файла с записями чатов.
# По умолчанию читает active_chats.txt и пишет только URLs в active_links.txt.

import re
import sys

# Параметры файлов
INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else 'active_chats.txt'
OUTPUT_FILE = sys.argv[2] if len(sys.argv) > 2 else 'active_links.txt'

# Регулярное выражение для поиска ссылок Telegram
pattern = re.compile(r'(https?://t\.me/\S+)')

with open(INPUT_FILE, 'r', encoding='utf-8') as fin, \
     open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:
    for line in fin:
        match = pattern.search(line)
        if match:
            fout.write(match.group(1) + '\n')

print(f"Готово: ссылки из '{INPUT_FILE}' сохранены в '{OUTPUT_FILE}'.")
