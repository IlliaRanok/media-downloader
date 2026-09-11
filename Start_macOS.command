#!/bin/bash
# Переходимо в директорію зі скриптом
cd "$(dirname "$0")"

# Запускаємо Python через віртуальне середовище
./.venv/bin/python3 media_downloader_app.py
