# strip_numbering.py
# Убирает префикс с нумерацией и точкой, оставляя только URL

import re
import sys

# Параметры файлов: по умолчанию читаем из 'links_with_nums.txt', выводим в 'links_clean.txt'
INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else 'links_with_nums.txt'
OUTPUT_FILE = sys.argv[2] if len(sys.argv) > 2 else 'links_clean.txt'

# Регекс для строк вида '123. https://t.me/...'
prefix_pattern = re.compile(r'^\s*\d+\.\s*(https?://\S+)')
# Общий регекс для URL в строке
url_pattern = re.compile(r'(https?://\S+)')

with open(INPUT_FILE, 'r', encoding='utf-8') as fin, \
     open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:
    for line in fin:
        line = line.rstrip('\n')
        m = prefix_pattern.match(line)
        if m:
            fout.write(m.group(1) + '\n')
        else:
            # если нет префикса, попробуем найти URL в строке
            u = url_pattern.search(line)
            if u:
                fout.write(u.group(1) + '\n')

print(f"Done: cleaned links written to '{OUTPUT_FILE}'")